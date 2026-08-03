# Build-time fonts

`web/static/fonts/` ships WOFF2 for the browser. Pillow's FreeType cannot read WOFF2, so the
Open Graph card renderer (`web/og.py`) needs the same face as TrueType. These are that copy:
build-time only, never served, so they cost the site nothing.

Keep the two in sync — the card is meant to look like the page.

Silkscreen, designed by Jason Kottke. Upstream copyright line, verbatim:

> Copyright 2001 The Silkscreen Project Authors
> (https://github.com/googlefonts/silkscreen)

Licensed under the SIL Open Font License 1.1. OFL §2 requires the licence to travel with every
redistributed copy, so `OFL.txt` sits beside the fonts here *and* beside the WOFF2 in
`web/static/fonts/` (which is served, so that copy is redistribution too).
Source: <https://fonts.google.com/specimen/Silkscreen>.
