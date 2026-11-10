# Automated catalogue data merges

**Goal:** Ship tested catalogue updates without manual approval and notify only on failure.

**Approach:** Keep the release-pointer PR and required release check. Explicitly dispatch
the check on the data branch with `actions: write`, because GitHub's bot PR events can
require human approval. After validating the published catalogue, a dependent job merges
the exact tested head through normal branch protection; no admin override or new token.

**Scope:** `.github/workflows/catalogue.yml`, `data-release-check.yml`, a small shared
`scripts/check_data_pr.py` guard, workflow regression tests, and the affected README/CLAUDE notes.

- [x] Add regression tests for guarded bot data-only PRs, existing-PR retry/dispatch,
  exact-head merge, foreign/code PR rejection, and changed-head rejection; observe RED.
- [x] Implement the dispatch/check/merge chain and failure-only Telegram steps.
- [x] Run the full suite, Ruff, Actionlint and parsed workflow-policy checks.
- [ ] Inspect the final diff, commit, push the complete branch, and create/link its PR.

**Safety boundaries:** Only open same-repository bot PRs targeting `main`, on
`data/refresh-` branches, changing exactly `data/RELEASE` qualify. Published data passes
the suite again against current main code before merge. Head changes or failed checks
block merge and notify Telegram. Existing pending data PRs are updated and retried by
the next probe. Ordinary source-code PRs never enter automatic merge.

**Activation:** This configuration starts after the setup PR reaches `main`. No live
catalogue workflow or test Telegram message is dispatched while preparing the PR.

Verification: full suite 841 passed, 24 skipped, 7 existing warnings; Ruff, Actionlint,
parsed workflow-policy assertions and 30 focused automation/transport tests passed.
