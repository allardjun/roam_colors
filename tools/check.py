#!/usr/bin/env python3
"""Integrity check for the two-tier theme system.

Silent failure is the norm in this repo — a stale Roam class, a dead
selector, a comment that ended early, or a colour that is 3.9:1 instead
of 4.5:1 all leave the page looking deliberately styled.  None of them
show up in a screenshot.  This checks the things a screenshot cannot.

    python3 tools/check.py            # check every entry file
    python3 tools/check.py glamour    # just one
    python3 tools/check.py -v         # show waived deviations too

What it checks, per entry file:

  contract    every application var components-v2.css consumes is
              defined here, and nothing beyond it except the handful of
              theme-local vars a theme is allowed to invent
  orphans     no --col-* entry is defined and never referenced
  duplicates  no var defined twice in :root (the cost is a silent
              override — see KNOWLEDGE.md "Variables-first design")
  contrast    every foreground measured against the surface it actually
              lands on, not against the page
  parse       tinycss2, if installed

Exit status is 1 if anything failed, so it can gate a commit.
"""

import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COMPONENTS = "components-v2.css"
REFERENCE = "base-v2.css"          # the entry file that defines the contract
ENTRIES = ["base-v2.css", "glamour.css", "argon-executive.css",
           "black-lotus-shock.css", "ukiyo-night.css", "cyanotype.css",
           "offprint.css"]

# A theme may invent vars for its own use — fonts it needs beyond the two
# in the contract, a hairline colour, and so on.  They are not part of the
# contract and components-v2.css must never reference them.
THEME_LOCAL = {"--font-display", "--font-serif", "--font-condensed",
               "--font-mono", "--rule-brass"}

MIN_TEXT = 4.5   # WCAG 1.4.3, text
MIN_SHAPE = 3.0  # WCAG 1.4.11, graphical objects and UI components

# Pairs of (foreground, background) application vars that carry text, with
# the surface each one actually lands on.  Getting this list right is the
# whole point: --emphasis is inline code drawn on --bg-raised, not on the
# page, and menu text is drawn on the light search card.
TEXT_PAIRS = [
    ("--text-primary",         "--bg-base"),
    ("--text-secondary",       "--bg-base"),
    ("--text-muted",           "--bg-base"),
    ("--text-body",            "--bg-base"),
    ("--title-fg",             "--bg-base"),
    ("--bold-fg",              "--bg-base"),
    ("--accent",               "--bg-base"),
    ("--success",              "--bg-base"),
    ("--emphasis",             "--bg-raised"),
    ("--keyword",              "--bg-base"),
    ("--error",                "--bg-base"),
    ("--special",              "--bg-base"),
    ("--string",               "--bg-base"),
    ("--table-text",           "--bg-base"),
    ("--text-body",            "--highlight-cool"),
    ("--text-body",            "--highlight-warm"),
    ("--text-on-light",        "--search-bg"),
    ("--text-on-accent",       "--accent"),
    ("--search-fg",            "--search-bg"),
    ("--search-fg-muted",      "--search-bg"),
    ("--keyword-on-light",     "--search-bg"),
    ("--search-selected-text", "--search-selected-bg"),
    ("--selection-text",       "--selection-bg"),
] + [("--cm6-" + t, "--cm6-bg") for t in
     ("fg", "muted", "keyword", "operator", "string", "variable",
      "number", "name", "type")]

# Not text.  A bullet and a tick mark are graphical objects, so the bar is
# WCAG's 3:1 for non-text contrast, not 4.5:1.  Holding a 6px dot to a
# body-text threshold is the wrong standard, not a stricter one.
SHAPE_PAIRS = [
    ("--bullet-outer",        "--bg-base"),
    ("--done-checkbox-check", "--done-checkbox-bg"),
    ("--done-checkbox-check", "--done-checkbox-border"),
]

# Known, deliberate deviations.  A waiver needs a reason, prints as a note
# rather than a failure, and is reviewable in one place — which is the
# point: these stay visible instead of being quietly dropped from the
# check.  Everything here is base-v2, and none of it is an oversight: the
# values come from Dracula and OneDark upstream, and changing them means
# shipping something that is no longer those palettes.  That is a design
# decision, not a bug fix.
WAIVERS = {
    ("base-v2.css", "--title-fg", "--bg-base"):
        "Dracula's own Comment #6272a4; recolouring page titles is a "
        "design change, not a fix. Worth revisiting — 3.03:1 is low for "
        "the largest text on the page.",
    ("base-v2.css", "--text-muted", "--bg-base"):
        "same Dracula Comment; noted in KNOWLEDGE.md.",
    ("base-v2.css", "--table-text", "--bg-base"):
        "inherited from base-v1; 4.22:1 is marginal, not invisible.",
    ("base-v2.css", "--search-fg-muted", "--search-bg"):
        "inherited from base-v1, which was 3.9:1; already raised once.",
    ("base-v2.css", "--cm6-muted", "--cm6-bg"):
        "OneDark's own comment grey, ported unmodified.",
    ("base-v2.css", "--selection-text", "--selection-bg"):
        "pale blue on steel blue, inherited from base-v1. This is the "
        "worst pair in the repo and the one most worth fixing: selected "
        "text is harder to read than unselected.",
    ("base-v2.css", "--bullet-outer", "--bg-base"):
        "collapsed bullets are dim in Dracula; glamour and the refactored "
        "themes deliberately raised theirs.",
}

# --text-on-accent-faded lands on the accent composited over the page at
# 0.7 opacity, so it is checked separately against that blend.
FADED_PILL = ("--text-on-accent-faded", "--accent", "--bg-base", 0.7)


# ── colour maths ────────────────────────────────────────────────────────

def _channel(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb(value):
    h = value.strip().lstrip("#")
    if len(h) == 8:          # #rrggbbaa — alpha is not composited here
        h = h[:6]
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(value):
    r, g, b = rgb(value)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast(fg, bg):
    a, b = luminance(fg), luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def composite(fg, bg, alpha):
    f, b = rgb(fg), rgb(bg)
    return "#%02x%02x%02x" % tuple(
        round(alpha * f[i] + (1 - alpha) * b[i]) for i in range(3))


# ── parsing ─────────────────────────────────────────────────────────────

DECL = re.compile(r"(--[a-z0-9-]+)\s*:\s*(.*?);", re.S)


def strip_comments(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def read(name):
    with open(os.path.join(REPO, name), encoding="utf-8") as fh:
        return fh.read()


def root_block(name):
    """The :root declarations of an entry file, comments removed."""
    src = strip_comments(read(name))
    match = re.search(r":root\s*\{(.*?)\n\}", src, re.S)
    if not match:
        raise SystemExit("%s: no :root block found" % name)
    return match.group(1)


def declarations(name):
    return dict(DECL.findall(root_block(name)))


def duplicates(name):
    names = [n for n, _ in DECL.findall(root_block(name))]
    return sorted({n for n in names if names.count(n) > 1})


def resolve(defs, var, seen=None):
    """Follow var() chains down to a literal value."""
    seen = seen or set()
    if var in seen or var not in defs:
        return None
    value = defs[var].strip()
    chain = re.fullmatch(r"var\((--[a-z0-9-]+)\)", value)
    if chain:
        return resolve(defs, chain.group(1), seen | {var})
    return value if value.startswith("#") else None


# ── checks ──────────────────────────────────────────────────────────────

def contract_vars():
    defs = declarations(REFERENCE)
    return {k for k in defs if not k.startswith("--col-")}


def components_uses():
    return set(re.findall(r"var\((--[a-z0-9-]+)\)",
                          strip_comments(read(COMPONENTS))))


def check_entry(name, contract, used):
    problems = []
    defs = declarations(name)
    app = {k for k in defs if not k.startswith("--col-")}
    palette = {k for k in defs if k.startswith("--col-")}

    for var in sorted(contract - app):
        problems.append("missing from the contract: %s" % var)
    for var in sorted(app - contract - THEME_LOCAL):
        problems.append("defined but not in the contract: %s "
                        "(add it to THEME_LOCAL if deliberate)" % var)
    for var in duplicates(name):
        problems.append("defined twice in :root: %s "
                        "(the later one silently wins)" % var)

    referenced = set(re.findall(r"var\((--[a-z0-9-]+)\)",
                                strip_comments(read(name)))) | used
    for var in sorted(palette - referenced):
        problems.append("orphan palette entry, never used: %s" % var)

    notes = []
    for pairs, floor in ((TEXT_PAIRS, MIN_TEXT), (SHAPE_PAIRS, MIN_SHAPE)):
        for fg, bg in pairs:
            a, b = resolve(defs, fg), resolve(defs, bg)
            if a is None or b is None:
                continue                   # non-literal (rgba, keyword) — skip
            ratio = contrast(a, b)
            if ratio >= floor:
                continue
            reason = WAIVERS.get((name, fg, bg))
            line = "%.2f:1  %s on %s  (needs %.1f)" % (ratio, fg, bg, floor)
            (notes if reason else problems).append(
                line + ("  — waived: " + reason if reason else ""))

    fg, accent, page, alpha = FADED_PILL
    a, ac, pg = resolve(defs, fg), resolve(defs, accent), resolve(defs, page)
    if None not in (a, ac, pg):
        ratio = contrast(a, composite(ac, pg, alpha))
        if ratio < MIN_TEXT:
            problems.append("%.2f:1  %s on the %.0f%%-opacity pill  (needs %.1f)"
                            % (ratio, fg, alpha * 100, MIN_TEXT))
    return problems, notes


def check_parse(name):
    try:
        import tinycss2
    except ImportError:
        return None
    with open(os.path.join(REPO, name), "rb") as fh:
        rules, _ = tinycss2.parse_stylesheet_bytes(fh.read(),
                                                   skip_whitespace=True)
    return [r for r in rules if r.type == "error"]


def main(argv):
    wanted = argv[1:]
    names = [w for w in wanted if not w.startswith("-")]
    entries = [e for e in ENTRIES
               if not names or any(w.rstrip(".css") in e for w in names)]
    if not entries:
        raise SystemExit("no entry file matches %s" % " ".join(wanted))

    contract, used = contract_vars(), components_uses()
    failed = False

    stray = sorted(u for u in used if u.startswith("--col-"))
    if stray:
        failed = True
        print("%s references the palette directly: %s"
              % (COMPONENTS, ", ".join(stray)))
    if used != contract:
        failed = True
        for var in sorted(used - contract):
            print("%s uses %s, which %s does not define"
                  % (COMPONENTS, var, REFERENCE))
        for var in sorted(contract - used):
            print("%s defines %s, which %s never uses"
                  % (REFERENCE, var, COMPONENTS))

    print("contract: %d application vars\n" % len(contract))

    verbose = "-v" in wanted or "--verbose" in wanted
    for name in entries:
        problems, notes = check_entry(name, contract, used)
        errors = check_parse(name)
        if errors:
            problems.append("parse errors: %s" % errors)
        if problems:
            failed = True
            print("  %s" % name)
            for problem in problems:
                print("      %s" % problem)
        else:
            tail = "" if errors is not None else "  (install tinycss2 to parse-check)"
            if notes:
                tail = "  (%d waived, -v to show)%s" % (len(notes), tail)
            print("  %-24s ok%s" % (name, tail))
        if notes and verbose:
            for note in notes:
                print("      note: %s" % note)

    errors = check_parse(COMPONENTS)
    if errors:
        failed = True
        print("  %s parse errors: %s" % (COMPONENTS, errors))

    print()
    print("FAIL" if failed else "all good")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
