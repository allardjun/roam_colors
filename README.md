# roam_colors

Custom CSS themes for [Roam Research](https://roamresearch.com).

Eight themes are current, and they all share one components file — the palette is very nearly the only thing that differs between them:

| Theme | Look |
|---|---|
| [`base-v2.css`](base-v2.css) | Dracula. Cool, dark, purple/cyan accents. |
| [`glamour.css`](glamour.css) | "Golden-Hour Neo-Deco" — espresso and black-marble surfaces, porcelain/crema type, champagne brass as the working metal, pink/teal/violet as rationed accents. Bodoni Moda titles over Montserrat body. |
| [`argon-executive.css`](argon-executive.css) | Charcoal lab bench, argon glow, chlorophyll. Nearly monochrome teal-green, with clay as the one warm color. |
| [`black-lotus-shock.css`](black-lotus-shock.css) | Black resin, violet neon, cyan HUD, amber warning LEDs. The darkest ground here; the color is rationed out as light sources. |
| [`ukiyo-night.css`](ukiyo-night.css) | Indigo ink, weathered paper, antique gold. Its neutral ramp changes hue as it climbs — indigo at the dark end, paper at the light end. |
| [`cyanotype.css`](cyanotype.css) | Prussian blue paper, white line work, and a drafting office's markup pencils — red for corrections, green for checked, amber for attention, violet for cross-references. IBM Plex in all three widths. The only saturated ground here, and the only theme whose bold text is a line weight rather than a color. |
| [`heads-down.css`](heads-down.css) | Graphite and a signal palette — a working screen at 11pm. The only exactly achromatic ramp here (R = G = B at all fourteen steps), sitting on VS Code Dark+'s ground and foreground, so a hue is never atmosphere and can only mean something: teal *resolved*, azure *referenced*, violet *declared*, amber *literal*, green *passing*, coral *failing*. Geist over Geist Mono, with teal monospace page titles. |
| [`offprint.css`](offprint.css) | **The light one.** A journal article: warm journal stock, cool process-black ink, hairline rules, and the colorblind-safe Okabe-Ito plate darkened to carry text on paper. Source Serif 4 for what you wrote; Public Sans in executive navy for every title and heading. |

## Installing

In Roam, create a page called `roam/css`, add a code block, switch its type to "CSS", and paste one of:

```css
@import url('https://allardjun.github.io/roam_colors/base-v2.css');
```

```css
@import url('https://allardjun.github.io/roam_colors/glamour.css');
```

…or any of the other six entry files in the table above.

Point the URL at an **entry file**, never at a components file — the entry file defines the variables and pulls in its own components.

## How the current themes are built

Two files, two tiers:

1. **Entry file** (any of the eight in the table) — a `:root` block split into a *palette* tier of raw colors (`--col-*`, the only place literal hexes appear) and an *application* tier of semantic roles (`--bg-raised`, `--accent`, `--search-selected-bg`) that map palette onto UI.
2. **Components** (`components-v2.css`) — every actual rule.
   It references only the semantic vars, never the palette and never a literal color.

So **a new theme is mostly a new palette**: copy an entry file, change the colors, keep the application map.
All eight share `components-v2.css` byte for byte and look nothing alike — including one that inverts the figure/ground relationship of every surface in the app.

"Mostly" is doing some work in that sentence.
Four of the eight carry a short theme-only section at the bottom of the entry file — glamour, cyanotype, offprint and heads-down, all of them for typographic or structural work that has no variable form.
The other four, base-v2 and the three palette themes, are `:root` and nothing else.
They used to carry overrides too, until it turned out five files were repeating the same two rules; those became `--bold-fg` and `--keyword-on-light` in the contract, and the files got shorter.

Two caveats, both learned the hard way:

- The entry file must define the **entire** application-var set the components file consumes, exactly by name.
  That set is the contract.
- Color-only isn't quite enough.
  Typographic and structural work — letter-spacing, hairline rules, tracked small caps — has no variable form.
  Put it in a clearly marked section at the bottom of the *entry* file so the other themes stay untouched.

Editing `components-v2.css` changes **every** current theme at once.
Commit such changes separately from whatever prompted them, so they can be reverted on their own.

### Also in this repo

- `base-v1.css` + `components.css` — the first split-layout version, kept frozen as a reference.
  Superseded by v2.
  They are a matched pair: nothing else imports `components.css`, so they move or go together.
  Frozen means frozen: fixes go into `components-v2.css`, never here.
- `RailsRoam.css` — a third-party theme kept purely as a reference for Roam's current class names.
  Not meant to be installed from here.

## Local prototyping

The GitHub Pages deploy round-trip is ~2 minutes, too slow to iterate.
Serve the repo over HTTPS from localhost instead:

```bash
brew install mkcert nss          # nss is for Firefox trust
mkcert -install                  # installs a local root CA into your keychain
cd /Users/jun/git/pub/roam_colors
mkcert localhost                 # creates localhost.pem + localhost-key.pem
npx http-server -S -C localhost.pem -K localhost-key.pem --cors -c-1 -p 8080
```

The `-c-1` disables server-side caching and you want it from the very first load — an entry already cached under the default `max-age=3600` stays "fresh" for an hour regardless.

Then swap the `@import` in your `roam/css` block to:

```css
@import url('https://localhost:8080/glamour.css');
```

If Roam renders completely unstyled, visit the URL directly in the same browser first and click through the certificate warning.
An untrusted cert makes the stylesheet fail **silently** as a subresource.

### The nested import caches separately

The entry file imports its components with a `?v=` on the URL:

```css
@import url('./components-v2.css?v=10');
```

That query string is load-bearing, not decoration.
The two files cache independently, so **editing `components-v2.css` is invisible until you bump that number** — and bump the `roam/css` import too, so the browser re-reads the entry file and discovers the new nested URL.
Changing only one of the two does nothing.
Each entry file carries its own tag (`?v=10`, `?v=g10`, `?v=ae2`, `?v=bls2`, `?v=un2`, `?v=cy2`, `?v=of2`, `?v=hd1`), so a components edit means bumping the tag in every entry file you are actually testing.
This has eaten several debugging sessions; see [KNOWLEDGE.md](KNOWLEDGE.md) for the full version, including the fact that the Roam desktop app keeps its own cache separate from any browser.

### Check your work with a parser

Silent failures are the norm here — a stale Roam class name, a dead selector, or a comment that ended early all leave the page looking deliberately styled.
A parse pass catches what a screenshot cannot:

```python
import tinycss2
rules, _ = tinycss2.parse_stylesheet_bytes(open('glamour.css','rb').read(),
                                           skip_whitespace=True)
print([r for r in rules if r.type == 'error'])
```

All of that is `tools/check.py`, which also measures every foreground against the surface it actually lands on:

```bash
python3 tools/check.py        # every entry file; exit 1 if anything fails
python3 tools/check.py -v     # show the waived deviations and their reasons
```

It verifies the application-var contract in both directions, finds orphan `--col-*` entries and duplicate definitions in `:root`, and parse-checks with tinycss2 when it is installed.
It also re-derives every `N.N:1` written in a comment and flags any that no longer matches a real pair, because those numbers rot silently when a palette entry changes late.
Known deviations live in a `WAIVERS` table in the script — each needs a written reason, and anything new fails loudly.

`tools/bump.sh` increments the `?v=` on every entry file at once, which is otherwise eight manual edits that fail silently when forgotten.

The `localhost.pem`, `localhost-key.pem`, and `rootCA*.pem` files should not be committed (see `.gitignore`).

## Notes

[KNOWLEDGE.md](KNOWLEDGE.md) collects how Roam's DOM and styling actually behave — Blueprint internals, which selectors are dead, caching traps, and what to check when a rule "doesn't work".
Read it before debugging anything in here.

`glamour.md` is the aesthetic brief `glamour.css` was derived from.

# Inspirations

https://jmharris903.github.io/Railscast-for-Roam-Research-Theme/RailsRoam.css

https://chatgpt.com/share/6a1eeef1-a880-83e8-bc66-15676c2c1d7e
