# roam_colors

Custom CSS theme for [Roam Research](https://roamresearch.com).

## Installing

In Roam, create a page called `roam/css`, add a code block, switch its type to "CSS", and paste:

```css
@import url('https://allardjun.github.io/roam_colors/dracula-jun.css');
```

## Local prototyping

The GitHub Pages deploy round-trip is ~2 minutes, which is too slow for iteration. Serve the repo over HTTPS from localhost instead:

```bash
brew install mkcert nss          # nss is for Firefox trust
mkcert -install                  # installs a local root CA into your keychain
cd /Users/jun/git/pub/roam_colors
mkcert localhost                 # creates localhost.pem + localhost-key.pem
npx http-server -S -C localhost.pem -K localhost-key.pem --cors -p 8080
```

Remove caching:

```bash
npx http-server -S -C localhost.pem -K localhost-key.pem --cors -c-1 -p 8080
```

Then swap the `@import` in your `roam/css` block to:

```css
@import url('https://localhost:8080/dracula-jun.css');
```

Edits to the local file are picked up on the next Roam reload (Cmd-R). Switch back to the GitHub Pages URL when done.

The `localhost.pem`, `localhost-key.pem`, and `rootCA*.pem` files should not be committed (see `.gitignore`).

# Inspirations

https://jmharris903.github.io/Railscast-for-Roam-Research-Theme/RailsRoam.css

https://chatgpt.com/share/6a1eeef1-a880-83e8-bc66-15676c2c1d7e
