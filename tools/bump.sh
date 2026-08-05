#!/usr/bin/env bash
# Bump the cache-buster on every entry file's components-v2.css import.
#
# The ?v= is load-bearing.  The entry file and the components file are
# cached independently, so an edit to components-v2.css stays invisible
# until the nested URL changes — and with seven entry files that is seven
# edits, each of which fails silently if you forget it.  See KNOWLEDGE.md
# "Caching gotcha".
#
#     tools/bump.sh          # bump every entry file
#     tools/bump.sh glamour  # just the ones whose name matches
#
# Remember the other half: bump the @import in your roam/css block too, or
# the browser never re-reads the entry file and never discovers the new
# nested URL.  Changing only one of the two does nothing.

set -euo pipefail
cd "$(dirname "$0")/.."

filter="${1:-}"
changed=0

for file in *.css; do
  grep -q "components-v2.css?v=" "$file" || continue
  [ -n "$filter" ] && case "$file" in *"$filter"*) ;; *) continue ;; esac

  before=$(sed -n 's/.*components-v2\.css?v=\([^'"'"']*\).*/\1/p' "$file" | head -1)
  prefix=$(printf '%s' "$before" | sed 's/[0-9]*$//')
  number=$(printf '%s' "$before" | sed 's/^[^0-9]*//')
  after="${prefix}$((number + 1))"

  # BSD and GNU sed disagree about -i, so write through a temp file.
  sed "s|components-v2\.css?v=${before}|components-v2.css?v=${after}|" \
      "$file" > "$file.tmp" && mv "$file.tmp" "$file"
  printf '  %-24s %s -> %s\n' "$file" "$before" "$after"
  changed=$((changed + 1))
done

if [ "$changed" -eq 0 ]; then
  echo "no entry files matched${filter:+ '"$filter"'}" >&2
  exit 1
fi

echo
echo "Now bump the @import in your roam/css block as well."
