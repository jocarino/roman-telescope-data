# Automated catalogue data merges

**Goal:** Ship tested catalogue updates without manual approval and notify only on failure.

**Approach:** Keep the release-pointer PR and required release check. Explicitly dispatch
the check on the data branch with `actions: write`, because GitHub's bot PR events can
require human approval. Validation creates and completes an explicit Checks API result
with `checks: write` for the required context, since dispatch job checks are excluded by
GitHub rulesets. After validating the published catalogue, a dependent job merges
the exact tested head through normal branch protection; no admin override or new token.

**Scope:** `.github/workflows/catalogue.yml`, `data-release-check.yml`, a small shared
`scripts/check_data_pr.py` guard, workflow regression tests, and the affected README/CLAUDE notes.

- [x] Add regression tests for guarded bot data-only PRs, existing-PR retry/dispatch,
  exact-head merge, foreign/code PR rejection, and changed-head rejection; observe RED.
- [x] Implement the dispatch/check/merge chain and failure-only Telegram steps.
- [x] Run the full suite, Ruff, Actionlint and parsed workflow-policy checks.
- [x] Inspect the final diff and commit the verified implementation.

Delivery: push the combined branch and open/link its setup PR against main.

**Safety boundaries:** Only open same-repository bot PRs targeting `main`, on
`data/refresh-` branches, changing exactly `data/RELEASE` qualify. Published data passes
the suite again against current main code before merge. Head changes or failed checks
block merge and notify Telegram. Existing pending data PRs are updated and retried by
the next probe. Ordinary source-code PRs never enter automatic merge.

**Activation:** This configuration starts after the setup PR reaches `main`. No live
catalogue workflow or test Telegram message is dispatched while preparing the PR.

Verification: full suite 843 passed, 24 skipped, 7 existing warnings; Ruff, Actionlint,
parsed workflow-policy assertions and 32 focused automation/transport tests passed.

Review correction: an independent reviewer identified that a successful dispatch job
alone cannot satisfy the active required-check ruleset. API-level pending/success/failure
reporting was added with regression tests, retaining the existing required app identity.
