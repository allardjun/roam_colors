# Roam styling knowledge

Notes on how Roam Research's DOM and styling system actually work, accumulated while maintaining this theme. Things you'd have to learn the hard way otherwise.

## The three layers

Roam's UI is a mash-up of three CSS namespaces, each with its own conventions:

1. **Blueprint.js** — `bp3-*` classes. This is [Palantir's React UI kit](https://blueprintjs.com), used for menus, tooltips, popovers, inputs, checkboxes, sliders, toasts, date pickers. Roam doesn't customize most Blueprint defaults, so retheming the app means retheming Blueprint.
2. **CodeMirror** — `.CodeMirror` container plus `.cm-*` token classes inside code blocks. The whole code-block experience (multiline ``` blocks) is rendered by CodeMirror 5, which has its own selection, cursor, gutter, and syntax-highlighting DOM.
3. **Roam-specific** — `rm-*` (modern) and `roam-*` (legacy). These are the only classes Roam itself authors. Everything else is third-party.

There is no published, stable selector taxonomy from Roam. Class names can change between versions. The community-maintained [Roam CSS System](https://github.com/rcvd/roam-css-system) tries to abstract this into ~700 CSS variables; most hand-rolled themes (including this one) just target classes directly and accept some breakage on Roam updates.

## Installation

Themes are loaded by creating a page literally named `roam/css` (lowercase, no spaces), adding a child block, switching its type to "CSS", and pasting either raw CSS or:

```css
@import url('https://example.com/theme.css');
```

Multiple `@import`s and raw blocks can coexist. Last one wins on conflicts (per normal CSS cascade).

Point the URL at an **entry file**, never at a components file — the entry file defines the variables and imports its components. Current entry files: `base-v2.css` (Dracula), `glamour.css` (Golden-Hour Neo-Deco), `argon-executive.css`, `black-lotus-shock.css`, `ukiyo-night.css`, `cyanotype.css`, `heads-down.css` and `offprint.css` (light). All eight share `components-v2.css`; `base-v1.css` + `components.css` are kept frozen as the pre-refactor reference.

## Specificity and `!important`

Many Roam/Blueprint defaults are themselves high-specificity (deep descendant selectors) or use inline styles. You will need `!important` more than you'd like, especially for:

- `.bp3-menu`, `.bp3-elevation-3` (popovers)
- `#buffer` (the bottom-right help/status widget)
- Anything Blueprint applies via inline `style="background-color: ..."`
- Selection (`::selection`) — Roam doesn't set it, but other styles can.

The cost: if you set the same property with `!important` in two places, the earlier one is silently dead. Watch out — the old `dracula-jun.css` had ~6 dead rules from this (the file is gone now; it is in git history if you want to see them). When you override an earlier rule with an `!important` version, delete (or comment-pointer to) the original.

## Bold text needs `strong, .rm-bold` and `!important`

Styling `<strong>` alone doesn't work — Roam applies an inline `color: rgb(...)` to bold elements, which beats any non-`!important` rule. Roam also sometimes wraps bold with a `.rm-bold` class instead of (or in addition to) `<strong>`. The robust pattern, lifted from RailsRoam.css:

```css
strong,
.rm-bold {
  color: var(--your-bold-color) !important;
}
```

Same pattern applies to other inline styles Roam sets — when CSS "doesn't work" on text formatting, the first thing to check in DevTools is whether Roam is applying an inline `style="color: ..."` that beats your rule.

## Page titles, including daily-note dates

`.rm-title-display` (display mode) and `.rm-title-textarea` (edit mode) target every page title — both regular pages and daily-note date pages. Roam doesn't expose a date-only class, so theming dates differently from other titles requires `:has()` content-matching, which is brittle. In practice, color all titles together.

**Title `color` is not won by `.rm-title-display`.** The displayed title is an `<h1>`, and the rule that actually paints it is **`.roam-body .roam-app h1`** (this is what RailsRoam.css uses). Setting `color` on `.rm-title-display` alone — even with `!important` — does *not* change the displayed title color, because `.roam-body .roam-app h1` is the governing selector for that element. To recolor titles, set `.roam-body .roam-app h1` (display) and keep `.rm-title-display, .rm-title-textarea` (edit-mode textarea + sidebar surfaces) pointing at the same var. In `base-v1.css` both feed `--title-fg`. Confirm with DevTools: the winning `color:` in the Styles pane is the `h1` rule, not `.rm-title-display`.

### Display and edit mode are two different elements

Roam renders the title as an `<h1>` and **swaps in a `<textarea>`** the
moment you click it. They are different elements, and a textarea does not
inherit `font-size` the way the h1 picks it up from Roam's own
stylesheet — so a theme that sets only family and color gets a title that
visibly shrinks on entering edit mode.

Set `font-size` on both, and `line-height` too, or it stops shrinking and
starts jumping vertically instead:

```css
.rm-title-display,
.rm-title-textarea {
  font-size: var(--title-size);
  line-height: 1.15;
}
```

The same applies to anything else you style on a title: padding, borders,
weight, tracking. If a property is set on only one of the two, clicking
the title will visibly change it. Roam does not expose the h1's own size,
so the value has to be chosen and eyeballed — keep it in one variable.

## Styling a whole block from a tag, with `:has()`

Roam puts the tag name in a `data-tag` attribute on the tag element, so
`:has()` lets the enclosing block react to a tag sitting inside it. This
gives you user-invokable styles — tag a block `#brand` and restyle the
whole thing:

```css
.rm-block-text:has([data-tag="brand"]),
.roam-block:has([data-tag="brand"]) {
  font-family: var(--font-display) !important;
  color: var(--brand-color) !important;
}

/* and hide the marker itself */
.rm-block-text:has([data-tag="brand"]) [data-tag="brand"] { display: none; }
```

Notes:

- Hide the tag with `display: none`, not transparency. A transparent tag
  still occupies its width — a gap mid-sentence — and is still selected
  and copied with the block.
- You do not lose the ability to edit it: Roam replaces the rendered
  block with a raw textarea on click, where the tag is plain text. So the
  rule only ever applies when you are *not* editing.
- Covers `#brand` and `#[[brand]]`, which carry the same `data-tag`.
  Plain `[[brand]]` is a page link, not a tag, and emits no `data-tag`.
- Needs a 2022-or-later engine for `:has()`. Current Chrome and the Roam
  desktop app are fine; older engines ignore the rule harmlessly.

## Block styles leak into children unless you scope through `.rm-block__self`

**This is the single easiest way to break a Roam theme.** A block's
container holds both its own content *and* its entire nested subtree:

```
.roam-block-container            <- .rm-heading-level-N lives HERE
├── .rm-block__self              <- this block's own content
│   └── .rm-block__input         <- the text you want to style
└── .rm-block-children           <- every descendant block
    └── .roam-block-container …
```

So `.rm-heading-level-1 .rm-block-text` does not mean "the heading's
text". It means "every block's text anywhere under this heading", and a
`# Heading` will drag its whole subtree into the heading's font. Scope
through `.rm-block__self`, which is a *sibling* of `.rm-block-children`:

```css
.rm-heading-level-1 > .rm-block__self .rm-block__input {
  font-family: var(--font-display) !important;
}
```

RailsRoam.css:1455 uses exactly this shape, for exactly this reason.

**Inherited properties leak even without a descendant selector.** Putting
`letter-spacing`, `font-family`, `color` or similar on the bare
`.rm-heading-level-N` container sends it down the whole subtree by normal
inheritance — block boundaries are not style boundaries. Children only
escape where some other rule sets that property on them directly (the
Typography block's `!important` on `.rm-block-text` masks font-family and
color, which is exactly why a leak can show up in tracking alone and look
baffling). Scope the container rule the same way.

Note the BEM pairing again: `.rm-block__input` is the current class,
`.rm-block-text` the older one. Inside `.rm-block__self`, listing both is
safe. `!important` is still needed to beat the Typography rules.

## Caching gotcha when iterating via `@import`

When using `@import url('...')` from `roam/css`, browser cache holds the imported sheet across normal reloads. Cmd-R won't always re-fetch. Two fixes:

- **Cmd-Shift-R** for a true hard reload that bypasses the cache.
- **Cache-bust the URL** — add `?v=2` (increment on each edit). This works even without a hard reload.
- **Disable caching at the server** — run `http-server` with `-c-1` (sets `max-age=-1`, i.e. no caching) so a plain Cmd-R always re-fetches. Best default while iterating. Caveat: it only affects fetches made *after* you set it — an entry already cached under the old `max-age=3600` stays "fresh" until its hour expires, so add `-c-1` *before* the first load (or clear the cache once).

### The split-file layout multiplies this

The entry file (any of the seven) `@import`s its components file, so **two** files are cached independently. Editing a component rule won't show up if you only cache-bust the entry — the nested sheet is held separately. To force the nested sheet to re-fetch you must change *its* URL, e.g. `@import url('./components.css?v=100')`, **and** bump the entry's `?v` so the browser re-reads the entry and discovers the new nested URL. Bumping only one of the two does nothing.

### The macOS desktop app caches separately from the browser

This burned an afternoon: the Roam **desktop app is Electron and keeps its own HTTP cache, independent of any browser**. The same `roam/css` `@import` can render correctly in a browser tab pointed at `roamresearch.com` while the desktop app shows a stale result — because the app cached the nested `components.css` earlier (under `max-age=3600`, before `-c-1`) and a parent `?v` bump never touched that nested URL. Symptom: "it works in the browser but not the app" with identical `roam/css`. Fix: cache-bust the nested import URL (above) so the app fetches a URL it has never seen, or iterate in the browser and use the app only for final checks. To see a `components.css` edit in the app you must bump *both* version numbers (parent in `roam/css` **and** the nested `?v=` in the entry file).

If you're running a local HTTPS server, the server's request log is the definitive test: a GET that hits it means the file is being re-fetched; silence means cache is winning. Note the log shows browser *and* app requests — match by timing to tell which client is (not) re-fetching.

## CodeMirror selection is two systems

Inside a code block, "selection" is rendered two different ways depending on whether CodeMirror or the browser owns focus:

- `.CodeMirror-selected` — the colored box CodeMirror draws under selected text.
- `.CodeMirror-line::selection` (and `::-moz-selection` for Firefox) — the browser's native text selection on the underlying DOM.

You need to style both, with both `-webkit-`/standard and `-moz-` variants. Skipping one leaves a visible "wrong color" flash during selection.

## The search menu's selected row is a class, not an inline style

Arrowing up/down through search results highlights a row. In current Roam
that row is `LI.bp3-menu-item.bp3-active`, inside
`UL.bp3-menu.rm-find-or-create__menu`. Two traps:

- **RailsRoam's approach is out of date.** It matches an inline
  `background-color: rgb(213, 218, 223)` on the row. Current Roam sets no
  inline background there at all — verified in the DOM — so any selector
  built on that never matches. (The block-autocomplete popover,
  `.bp3-elevation-3 .dont-unfocus-block`, *does* still use an inline
  style, so both forms are in play on different surfaces. Match it
  loosely, `[style~="background-color:"]`, so it survives Roam changing
  the value.)
- **`!important` alone is not enough.** Roam styles the active row
  through its own `rm-find-or-create__menu` class, so a bare
  `.bp3-menu-item.bp3-active { ... !important }` still loses. Qualify the
  selector (e.g. `.bp3-menu li.bp3-menu-item.bp3-active`).

Also: `#d5dadf` is Roam's own highlight grey. Don't reuse it as your
hover color — base-v1 did, which made keyboard selection 1.16:1 against
the menu background and effectively invisible.

## Popover arrows need `fill`, not `color`

`.bp3-popover-arrow { color: ... }` is a **no-op**. Blueprint paints the
arrow as an SVG `<path class="bp3-popover-arrow-fill">`, so it needs
`.bp3-popover .bp3-popover-arrow-fill { fill: ... }`. base-v1 had the
`color` form, which is why every popover in Roam — date picker, tooltips,
block menus — rendered a white triangle against the dark theme.

## Blueprint date picker: don't bother with day cells

Theming the day cells (today / selected / hover / outside-month) was
tried in v2 and reverted. Each fix uncovered another Blueprint layer:

- Fill and text render on the inner `.bp3-datepicker-day-wrapper`. A
  background on `.DayPicker-Day` is hidden behind it.
- Setting it on both leaks a square behind the wrapper's round chip —
  the cell is rectangular, the wrapper isn't.
- Blueprint also draws a light focus indicator on the cell above the
  wrapper, which the cell background had been masking. Remove the
  background and a bright white square appears on the focused day.

Net result looked worse than the untouched Blueprint defaults. The panel
(`.bp3-datepicker`) and the month/year selects are worth theming; the day
grid is not, unless you're willing to design the whole thing.

## Roam moved some class names to BEM, and stale ones fail silently

Roam renamed part of its class vocabulary to BEM-ish double-dash /
double-underscore forms without removing the old markup everywhere:

| Pre-BEM | Current |
|---|---|
| `.rm-page-ref-link-color` | `.rm-page-ref--link` |
| `.rm-page-ref-brackets` | `.rm-page-ref__brackets` |
| `.rm-page-ref-namespace-color` | `.rm-page-ref--namespace` |

This bit base-v1 and base-v2 for their whole lives: both styled page
links via `.rm-page-ref-link-color`, which current Roam never emits, so
`--special` never reached a single `[[link]]`. They fell through to the
`.rm-page-ref` wrapper and rendered as `--text-muted` instead — the same
color as ordinary de-emphasised text, which also costs the link its
affordance. Fixed by listing both spellings.

**The general hazard is the silent failure.** A stale class name does not
error and does not leave the element unstyled — the element keeps its
inherited or wrapper color, so the page still looks deliberately themed.
The rule appears to work. The only reliable check is to inspect the
element and confirm the selector actually matches, rather than eyeballing
the render and assuming a plausible-looking color came from your rule.

Corollary: when a color looks "close enough but not quite right", suspect
a dead selector before suspecting the value.

## Validate with a CSS parser, not with your eyes

Both silent failures found while building `glamour.css` were invisible in
the render. A quick parse pass catches things no screenshot will:

```python
import tinycss2
rules, _ = tinycss2.parse_stylesheet_bytes(open('theme.css','rb').read(),
                                           skip_whitespace=True)
print([r for r in rules if r.type == 'error'])
```

**CSS comments do not nest, and a literal comment-close sequence inside a
comment ends it right there.** `base-v2.css` had a changelog line quoting
a comment marker; it terminated the block 15 lines early and the rest of
the prose was parsed as stray CSS. Nothing broke only because it sat at
end-of-file — any rule appended after it would have been silently
swallowed. If you need to mention a comment delimiter in prose, describe
it instead of quoting it.

Worth pairing with a variable-integrity check, since the two-tier layout
makes both failure modes easy: every `var()` used by the components file
is defined by the entry file, no application var is defined and unused,
no palette entry is orphaned, and the components file never references
`--col-*` directly.

All of that, plus contrast, is `tools/check.py` — run it rather than
re-deriving it.

## Designing more themes on the same components

`glamour.css` was built as a pure palette swap over the same
`components-v2.css`, which validated the two-tier idea — but four things
only show up once you try it.

**Contrast must be measured against the surface the color actually lands
on, not against the page background.** Inline code is drawn on
`--bg-raised`, not `--bg-base`; menu text is drawn on the light search
card. A palette can look fine as a swatch row and still fail in place.

**Watch for one var used on two different surfaces.** `--keyword` paints
both the linked-ref page title (dark page) and the "Create page" label
(light search card). No single value can clear 4.5:1 on both — the
requirements point in opposite directions. The fix is a second, adjusted
value applied by a narrow rule for the minority surface, not a compromise
value that is mediocre on each.

**On a dark theme, dark accents can only be backgrounds.** A brand
palette will happily hand you deep colors that are unusable as text on a
near-black ground. Those become your filled states — selected rows,
highlights, checkboxes — while only the light end of the palette can
carry text. Sort the palette by luminance before assigning roles; the
ordering tells you which colors are foreground candidates at all.

**`--font-ui` is set with `!important` on `body`/`.roam-app`, which drags
it into code surfaces.** If the theme's UI font is not monospace, code
and inline code need the mono stack re-asserted explicitly.

**A darker background makes the same text color read as harsher.**
`glamour.css` and `base-v2.css` both use a near-white body text, but
glamour's page is much darker (relative luminance .007 vs .026), so
identical text lightness buys noticeably more contrast — 13.2:1 against
10.9:1. It looked over-bright next to the older theme even though
nothing was wrong with the value. **Matching two dark themes by eye means
deliberately not matching them by hex**; compare the computed ratios, not
the colors.

**What bounds how far you can dim body text is not the page background.**
It is whatever body text also sits on — highlight marks, raised panels.
Dimming glamour's body text hit its floor around 11:1 against the page,
because below that, text on the teal highlight drops under 4.5:1. Check
the secondary surfaces before deciding a text color is safe to darken.

Web fonts work: an `@import` of a Google Fonts URL in the entry file is
fine, as long as it sits with the other `@import`s before any rule. It is
the only external dependency in these themes, so keep a real fallback
stack behind it.

### A light theme is the real test, and the system passed it

`offprint.css` inverts the figure/ground relationship of every surface in the app, and `components-v2.css` needed **no changes at all**.
That is a much stronger result than a palette swap, which only shows the system survives a change of hue.

The reason it works is that the application vars are named for *roles*, not for directions.
`--bg-raised` means "the surface a popover and an inline-code chip sit on"; on a dark theme that is lighter than the page and on a light theme it is a shade darker, and no rule cares.
The same holds for `--text-on-accent`, `--search-selected-bg` and the rest.

**One var did break, and it is the one that names two roles.**
`--bullet-inner` is the open bullet *and* the background of the slider's value chip, whose text is `--text-on-light`.
On a dark theme both roles want a light value, so the overload is invisible.
On a light theme they want opposites: a bullet on paper has to be dark to be seen, which leaves the chip dark with dark text on it.
If a var has to be described with the word "and", that is the bug — split it before a theme finds it for you.

**Two problems disappear entirely on a light theme.**
The "Create page" label needs no deepened value, because that whole class of bug only exists when a light island sits inside a dark theme.
And the Blueprint date-picker day cells this file gives up on look intentional, because their untouched light-mode defaults finally match what is around them.

### On a light ground, only the *dark* end of a palette can carry text

The mirror of the rule above about dark themes, and it bites harder, because the palettes worth borrowing are designed for fills.

`offprint.css` uses Okabe-Ito, the colourblind-safe qualitative set that scientific figure guidelines standardised on.
Measured as text on its journal-stock ground, **six of its seven hues fail**: yellow at 1.2:1, orange 2.0, sky blue 2.1, purple 2.8, green 3.1, vermilion 3.5, and only blue passes at 4.7.
Every member had to be darkened, with the original kept in a comment.

Sort the palette by luminance before assigning roles, in either direction.
The ordering tells you which colours are foreground candidates at all.

### When most of your themes override the same rule, the rule wants a variable

Five of seven entry files had carried an identical `strong, .rm-bold` override, and five an identical "Create page" label override — the same selectors, copy-pasted.
Both are now `--bold-fg` and `--keyword-on-light` in the contract, and the entry files are shorter for it.

The bold case is worth understanding because it will recur.
`--special` has to stay mid-toned so it can double as the page-link colour, while `--text-body` sits at the extreme end of the ramp.
So on any theme with genuinely high body contrast, painting bold with `--special` makes bold **lower contrast than the sentence around it** — emphasis measurably quieter than what it emphasises.
Three themes hit this independently before it was diagnosed.

### Check the whole matrix, not the theme you are working on

`tools/check.py` verifies the contract in both directions, finds orphan and duplicate vars, and measures every foreground against the surface it actually lands on.
Run it before committing; it is the only thing that catches a 3.9:1 that looks fine on your monitor.

Its first run found that **`base-v2.css` has the worst contrast in the repo** — seven pairs below threshold, including page titles at 3.03:1 and selected text at 1.96:1 against its own selection background, which makes selected text harder to read than unselected.
Those values come from Dracula and OneDark upstream, so they are recorded as waivers with written reasons rather than silently changed; changing them means shipping something that is no longer those palettes.
The lesson is the ordering: the theme nobody was editing was the one with the problems, and no amount of looking at it would have surfaced them.

Two thresholds, not one.
Text is WCAG 1.4.3's 4.5:1; bullets, tick marks and other graphical objects are 1.4.11's 3:1.
Holding a 6px dot to a body-text standard is the wrong measure, not a stricter one.

### The contrast numbers written in the comments rot, and nothing notices

Every `N.N:1` in these files is an assertion about a measured value, and the assertions decay the moment a palette entry changes.
Deepen one hex late in the session and every sentence quoting the old figure is now a lie that parses, validates, renders correctly and looks authoritative.

Building `heads-down.css` produced seventeen of them in a single sitting, purely from adjusting two palette entries — `--col-n900` and the coral — after the comments around them were already written.
A sweep across the rest of the repo then found six more that had been committed and pushed weeks earlier.

`tools/check.py` now re-derives them: it computes the contrast of every pair of literal-valued vars in a file, rounds to the precision the comments use, and flags any claim matching none of them.
It reports these as notes rather than failures, because a claim can be legitimate and unmatchable — `glamour.css` cites base-v2's body contrast to explain why it diverged, and a cross-file reference is invisible to a single-file matcher.

The general lesson is worth more than the specific check.
**A number written in prose next to the code is not documentation, it is an untested assertion.**
If it is worth writing down, it is worth re-deriving; if it cannot be re-derived, expect it to be wrong within two sessions.

### An achromatic ramp is a design constraint, not an absence of one

Six of the eight themes here tint their greys — a teal charcoal, an indigo black, an espresso brown.
`heads-down.css` holds R = G = B at all fourteen steps instead, and the consequence is not that the theme looks plainer but that it can make a stronger claim: with no tint anywhere in the neutrals, a hue on the page cannot be read as atmosphere and can only be read as a signal.

That turns the palette into a budget with meanings attached rather than a mood board, which in turn decides questions that are otherwise arbitrary — headings get no colour, and code comments are grey rather than the green every editor uses, because under the rule a comment is prose.

The constraint is also mechanically checkable, which the mood is not: `len(set(rgb(value))) == 1` at every step.
Prefer premises you can assert in code.

## Useful class map (the ones that aren't obvious)

| What you want to style | Selector |
|---|---|
| Top bar | `.roam-topbar` |
| Left sidebar | `.roam-sidebar-container` |
| Right sidebar | `#right-sidebar > div` |
| Bottom-right help widget | `#buffer` |
| Main column | `.roam-body-main` / `.roam-app` |
| Block reference (((...))) | `.rm-block-ref` |
| Page reference [[...]] | `.rm-page-ref` (wrapper), `.rm-page-ref--link` (the link text), `.rm-page-ref__brackets` — see the BEM note above; the pre-BEM `.rm-page-ref-link-color` / `.rm-page-ref-brackets` are dead in current Roam |
| Horizontal rule (`---`) | `.rm-hr` — a bare `hr` selector loses to it on specificity |
| Linked refs section | `.rm-reference-item`, `.rm-ref-page-view-title` |
| All Pages table | `.rm-all-pages`, `.rm-pages-row`, `.rm-pages-title-col`, `.rm-pages-col` |
| Find-or-create palette | `.rm-find-or-create-wrapper` |
| Mention pills (in All Pages) | `.rm-clickable-pill` with `.level1-pill` / `.level2-pill` / `.level3-pill` |
| Embed | `.rm-embed-container` (nests on itself) |
| TODO/DONE checkbox | `.check-container`, `.checkmark`, `input:checked ~ .checkmark` |
| Blueprint checkbox (table rows) | `.bp3-control.bp3-checkbox .bp3-control-indicator` |
| Bullet (open) | `.simple-bullet-outer .simple-bullet-inner` |
| Bullet (closed/collapsed) | `.roam-bullet-closed` |
| Indent guide line | `.block-border-left` |
| Block highlight (^^...^^) | `.roam-highlight`, `.block-highlight-yellow/blue/grey` |
| Page title input | `.rm-title-display`, `.rm-title-textarea` |
| In-block headings | `.rm-heading-level-1` / `-2` / `-3` |
| Block text | `.rm-block__input` (current) / `.rm-block-text` (older) |
| A block's own content, excluding children | `.rm-block__self` — see the leak note above |
| A block's nested children | `.rm-block-children` |
| Sync indicator | `.rm-saving-inner-icon.rm-synced` / `.rm-saving-remote` |
| Intercom widget (to hide) | `.intercom-app`, `.intercom-launcher-frame`, `#intercom-container` |

CodeMirror tokens you'll actually see in Roam code blocks: `cm-keyword`, `cm-atom`, `cm-number`, `cm-def`, `cm-variable-2/3`, `cm-type`, `cm-comment`, `cm-string`, `cm-string-2`, `cm-meta`, `cm-qualifier`, `cm-builtin`, `cm-bracket`, `cm-tag`, `cm-attribute`, `cm-hr`, `cm-link`, `cm-error`, `cm-header`. Scope them under `.cm-s-default` so they don't apply to other themes.

## Variables-first design

Define everything in a single `:root` block. The cost of a duplicate variable name in the same `:root` is silent override — easy to ship a bug where the "wrong" definition wins. Resist the urge to add a second `:root` further down the file when you add a new feature; just append the variable to the top one.

### Two tiers: palette vs application

Entry files (`base-v1.css`, `base-v2.css`, `glamour.css`) split their `:root` into two tiers, and themes built on this repo should follow the same convention:

1. **Palette** — raw, color-describing hues, prefixed `--col-*` (e.g. `--col-cyan: #8be9fd`). One entry per distinct hex; this is the *only* place literal colors appear.
2. **Application** — semantic role vars that map palette → UI (e.g. `--accent: var(--col-cyan)`, `--bg-raised: var(--col-slate)`). Component rules reference *only* these. Each application var carries a comment listing where it's used, so the block doubles as a map of which components share a color.

Components live in a separate `components.css` (see below) and never touch the palette directly. **To make a new theme, change only the palette tier** — the application map and components stay put. (Group application vars by shared color: roles that are meant to track the same hue in every theme share one application var.)

**How well this holds up in practice:** `glamour.css` and `base-v2.css` are entirely different-looking themes sharing one unmodified `components-v2.css`, so the core claim is real. Two caveats learned building the second one:

- A new theme must define the *entire* application-var set the components file consumes, exactly by name — that set is the contract. Diff the two entry files' non-`--col-*` names; the difference should be empty in both directions.
- Color-only is not quite enough. Anything typographic or structural — letter-spacing, hairline rules, small caps — cannot be expressed as a variable. Put those in a clearly-marked section at the bottom of the *entry* file rather than in the shared components file, so the other themes stay untouched.

When a fix genuinely belongs to the shared components file, remember it changes every theme at once. Commit it separately from the theme that prompted it so it can be reverted on its own.

### `@import` must precede `:root`

Every entry file pulls in its components with `@import url('./components-v2.css?v=…')` at the very top, *before* the `:root` block. A CSS `@import` is silently dropped by the browser if any style rule (including `:root`) precedes it. This is safe because custom-property resolution is order-independent: `var()` resolves at used-value time against the single `:root`, so `components.css` (imported first) still sees vars defined just below. The relative path resolves against the entry file's own URL, so it works on GitHub Pages and the localhost dev server alike — the install URL is unchanged.

## Local prototyping

Iterating through GitHub Pages takes ~2 minutes per change. Two faster paths:

- **[Stylus](https://add0n.com/stylus.html) browser extension** — paste CSS into the editor, scope to `roamresearch.com`, refresh. Live preview means no Roam reload between edits. Best for exploratory work.
- **Local HTTPS server** — `mkcert` + `npx http-server -S ...` and `@import` from `https://localhost:8080/...`. See [README.md](README.md). Best when you want to edit the actual file in your repo.

Plain HTTP doesn't work — Roam is HTTPS and the browser blocks mixed content.

## What to be skeptical of

- Class names ending in numeric suffixes (`-level1-pill`, `cm-variable-2`) are stable-ish but can be renamed.
- `bp3-*` will eventually become `bp4-*` or `bp5-*` if Roam upgrades Blueprint — be ready for a search-and-replace day.
- `roam-*` (no `rm-` prefix) classes are older and have been getting phased out. New work should target `rm-*` when both exist.
- Inline-style overrides from Roam will defeat your CSS without `!important`. Always check the computed styles panel in DevTools, not just the cascade view.
