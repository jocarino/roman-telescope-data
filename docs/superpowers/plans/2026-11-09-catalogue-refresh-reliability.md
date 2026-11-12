# Catalogue refresh reliability implementation plan

**Goal:** Fix the seven accepted review findings without publishing or deploying data.

**Architecture:** Keep the scheduled Python build and release-pointer PR. Compare the
Archive against the release pinned in `data/RELEASE`. Hash complete input rows, retain
the snapshot of the bulk build's actual fetched rows in its provenance, and derive
release manifests from that saved snapshot. Share only Telegram transport validation.

**Constraints:** Python 3.11+, standard library and existing dependencies; no live
notifications, workflow dispatches, dataset publication, or pushes to main.

## Tasks

- [x] Replace aggregate fingerprints with complete per-planet hashes, including safe
  migration from old manifests. Test metadata revisions, cancelling changes, stable
  ordering, additions, removals, and genuine revisions through the emitted TAP query.
- [x] Retain a bulk build's fetched input snapshot through
  manifest generation and manual publishing. Test late arrivals and refuse to invent
  a snapshot for older artifacts; update only rebuilt rows' hashes during partial merges.
- [x] Pin both workflow downloads and CLI baseline loading to `data/RELEASE`, and fail
  on download or missing-baseline errors. Exercise workflow shell blocks with fake `gh`.
- [x] Cover probe failures with an alert and validate Telegram HTTP/JSON responses in
  both workflows. Test against fake transport, never send real messages.
- [x] Update affected docs and CLI messages, run the full pytest suite and Ruff,
  validate workflow/shell syntax, and review the final diff for all seven requirements.

## Verification focus

Old aggregate manifests must request one rebuild. A build must not acknowledge a
later Archive snapshot. Failed downloads must keep the shrink guard active. Healthy
no-change/open-PR runs must stay silent. Failed alerts must never log delivery success.

## Execution record

- Existing focused baseline: 54 tests passed during review; rechecking in this worktree.
- Ruling: retain the actual input rows' hashes in `planets.json` provenance, so manual
  publishing cannot substitute current Archive state for an older artifact. This also
  handles cached inputs correctly and needs no additional pre-build network request.
- Replaced obsolete aggregate-fingerprint unit tests with SQLite-backed query tests;
  an existing test accidentally called NASA and failed with HTTP 522 in the baseline.
- Ruff, Actionlint, YAML parsing and release-script syntax checks passed. README
  fact-checking has the same one error and two warnings as the unchanged baseline.

- Full suite: 829 passed, 24 skipped, 7 existing colour-library warnings. The 55 new
  regression cases cover the seven fixes and their callers. Ruff and Actionlint passed.
- The initial independent final review found no issues. Two subsequent independent
  reviews reproduced a partial-merge false negative when the Archive reverts a value.
  The fix updates rebuilt rows' hashes and preserves all others, including with `--limit`.
  Existing open-PR suppression and the 10,000-row build cap remain.
- Changes stay on the local branch; no publication, live notification, or deployment.

- Follow-up: the 5000 → 5100 → 5000 correction regression failed before the fix and
  passed after updating consumed rows' hashes. Coverage includes new planets, untouched
  rows, `--limit`, and refusal to invent a missing bulk snapshot. Full suite and Ruff pass.
