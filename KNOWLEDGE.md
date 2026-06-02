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

## Specificity and `!important`

Many Roam/Blueprint defaults are themselves high-specificity (deep descendant selectors) or use inline styles. You will need `!important` more than you'd like, especially for:

- `.bp3-menu`, `.bp3-elevation-3` (popovers)
- `#buffer` (the bottom-right help/status widget)
- Anything Blueprint applies via inline `style="background-color: ..."`
- Selection (`::selection`) — Roam doesn't set it, but other styles can.

The cost: if you set the same property with `!important` in two places, the earlier one is silently dead. Watch out — `dracula-jun.css` had ~6 dead rules from this. When you override an earlier rule with an `!important` version, delete (or comment-pointer to) the original.

## CodeMirror selection is two systems

Inside a code block, "selection" is rendered two different ways depending on whether CodeMirror or the browser owns focus:

- `.CodeMirror-selected` — the colored box CodeMirror draws under selected text.
- `.CodeMirror-line::selection` (and `::-moz-selection` for Firefox) — the browser's native text selection on the underlying DOM.

You need to style both, with both `-webkit-`/standard and `-moz-` variants. Skipping one leaves a visible "wrong color" flash during selection.

## Useful class map (the ones that aren't obvious)

| What you want to style | Selector |
|---|---|
| Top bar | `.roam-topbar` |
| Left sidebar | `.roam-sidebar-container` |
| Right sidebar | `#right-sidebar > div` |
| Bottom-right help widget | `#buffer` |
| Main column | `.roam-body-main` / `.roam-app` |
| Block reference (((...))) | `.rm-block-ref` |
| Page reference [[...]] | `.rm-page-ref`, `.rm-page-ref-brackets`, `.rm-page-ref-link-color` |
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
| Block text | `.rm-block-text` |
| Sync indicator | `.rm-saving-inner-icon.rm-synced` / `.rm-saving-remote` |
| Intercom widget (to hide) | `.intercom-app`, `.intercom-launcher-frame`, `#intercom-container` |

CodeMirror tokens you'll actually see in Roam code blocks: `cm-keyword`, `cm-atom`, `cm-number`, `cm-def`, `cm-variable-2/3`, `cm-type`, `cm-comment`, `cm-string`, `cm-string-2`, `cm-meta`, `cm-qualifier`, `cm-builtin`, `cm-bracket`, `cm-tag`, `cm-attribute`, `cm-hr`, `cm-link`, `cm-error`, `cm-header`. Scope them under `.cm-s-default` so they don't apply to other themes.

## Variables-first design

Define everything in a single `:root` block. The cost of a duplicate variable name in the same `:root` is silent override — easy to ship a bug where the "wrong" definition wins. Resist the urge to add a second `:root` further down the file when you add a new feature; just append the variable to the top one.

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
