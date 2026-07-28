# Build-time fonts

`web/static/fonts/` ships WOFF2 for the browser. Pillow's FreeType cannot read WOFF2, so the
Open Graph card renderer (`web/og.py`) needs the same face as TrueType. These are that copy:
build-time only, never served, so they cost the site nothing.

Keep the two in sync — the card is meant to look like the page.

Silkscreen by Jason Kottke, licensed under the SIL Open Font License 1.1
(<https://openfontlicense.org>). Source: <https://fonts.google.com/specimen/Silkscreen>.
