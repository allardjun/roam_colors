# roam_colors

Custom CSS themes for [Roam Research](https://roamresearch.com).

Two themes are current, and they share their component rules — the palette
is the only thing that differs between them:

| Theme | Look |
|---|---|
| [`base-v2.css`](base-v2.css) | Dracula. Cool, dark, purple/cyan accents. |
| [`glamour.css`](glamour.css) | "Golden-Hour Neo-Deco" — espresso and black-marble surfaces, porcelain/crema type, champagne brass as the working metal, pink/teal/violet as rationed accents. Bodoni Moda titles over Montserrat body. |

## Installing

In Roam, create a page called `roam/css`, add a code block, switch its type
to "CSS", and paste one of:

```css
@import url('https://allardjun.github.io/roam_colors/base-v2.css');
```

```css
@import url('https://allardjun.github.io/roam_colors/glamour.css');
```

Point the URL at an **entry file**, never at a components file — the entry
file defines the variables and pulls in its own components.

## How the current themes are built

Two files, two tiers:

1. **Entry file** (`base-v2.css`, `glamour.css`) — a `:root` block split into
   a *palette* tier of raw colors (`--col-*`, the only place literal hexes
   appear) and an *application* tier of semantic roles (`--bg-raised`,
   `--accent`, `--search-selected-bg`) that map palette onto UI.
2. **Components** (`components-v2.css`) — every actual rule. It references
   only the semantic vars, never the palette and never a literal color.

So **a new theme is mostly a new palette**: copy an entry file, change the
colors, keep the application map. `glamour.css` and `base-v2.css` look
nothing alike and share `components-v2.css` byte for byte.

Two caveats, both learned the hard way:

- The entry file must define the **entire** application-var set the
  components file consumes, exactly by name. That set is the contract.
- Color-only isn't quite enough. Typographic and structural work —
  letter-spacing, hairline rules, tracked small caps — has no variable
  form. Put it in a clearly marked section at the bottom of the *entry*
  file so the other themes stay untouched.

Editing `components-v2.css` changes **every** current theme at once. Commit
such changes separately from whatever prompted them, so they can be
reverted on their own.

### Also in this repo

- `base-v1.css` + `components.css` — the first split-layout version, kept
  frozen as a reference. Superseded by v2.
- `dracula-jun.css` and its palette variants `argon-executive.css`,
  `black-lotus-shock.css`, `ukiyo-night.css` — the older monolithic
  themes, each a single self-contained file with no shared components.
  Still installable, but they predate the refactor and don't benefit from
  fixes made to `components-v2.css`.
- `RailsRoam.css` — a third-party theme kept purely as a reference for
  Roam's current class names. Not meant to be installed from here.

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

The `-c-1` disables server-side caching and you want it from the very first
load — an entry already cached under the default `max-age=3600` stays
"fresh" for an hour regardless.

Then swap the `@import` in your `roam/css` block to:

```css
@import url('https://localhost:8080/glamour.css');
```

If Roam renders completely unstyled, visit the URL directly in the same
browser first and click through the certificate warning. An untrusted cert
makes the stylesheet fail **silently** as a subresource.

### The nested import caches separately

The entry file imports its components with a `?v=` on the URL:

```css
@import url('./components-v2.css?v=9');
```

That query string is load-bearing, not decoration. The two files cache
independently, so **editing `components-v2.css` is invisible until you bump
that number** — and bump the `roam/css` import too, so the browser re-reads
the entry file and discovers the new nested URL. Changing only one of the
two does nothing. This has eaten several debugging sessions; see
[KNOWLEDGE.md](KNOWLEDGE.md) for the full version, including the fact that
the Roam desktop app keeps its own cache separate from any browser.

### Check your work with a parser

Silent failures are the norm here — a stale Roam class name, a dead
selector, or a comment that ended early all leave the page looking
deliberately styled. A parse pass catches what a screenshot cannot:

```python
import tinycss2
rules, _ = tinycss2.parse_stylesheet_bytes(open('glamour.css','rb').read(),
                                           skip_whitespace=True)
print([r for r in rules if r.type == 'error'])
```

The `localhost.pem`, `localhost-key.pem`, and `rootCA*.pem` files should not
be committed (see `.gitignore`).

## Notes

[KNOWLEDGE.md](KNOWLEDGE.md) collects how Roam's DOM and styling actually
behave — Blueprint internals, which selectors are dead, caching traps, and
what to check when a rule "doesn't work". Read it before debugging anything
in here.

`glamour.md` is the aesthetic brief `glamour.css` was derived from.

# Inspirations

https://jmharris903.github.io/Railscast-for-Roam-Research-Theme/RailsRoam.css

https://chatgpt.com/share/6a1eeef1-a880-83e8-bc66-15676c2c1d7e
