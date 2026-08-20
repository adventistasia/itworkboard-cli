## Residual Review Findings

**Branch:** `feat/embed-default-credentials`
**Run:** `20260820-232554-7115`
**Date:** 2026-08-20

### Decision-gate findings (require user decision)

- **P1** `config/workboard.defaults.yaml:13` — Live org Azure AD client_id + tenant_id embedded in committed defaults of a public repo. The repo is public, and while client_id is not a secret (public client app, device-code flow), committing the org's live identifiers turns the app registration into a universally usable auth primitive. **Requires decision:** ship placeholder identifiers, or harden the app registration (MFA/conditional access) and qualify the README for external users.
- **P2** `readme.md:35` — README tells every public-repo user the CLI ships with "default credentials" and needs no setup, funneling external identities into the org tenant. Related to the above — if credentials are shipped, the README should be qualified for external users.

### Applied fixes (step 5)

- #2: Updated troubleshooting.md to mention defaults-first flow
- #3: Added missing local-file-fall-through test
- #4: Updated example config header for defaults-first flow
- #5: Updated configuration.md file structure
- #6: Clarified CWD-conditional claim in README
- #8: Updated config.py error message
- #9: Added smoke test for real defaults file
- #10: Extracted shared DEFAULTS_DICT fixture
- #11: Replaced brittle call-count mock with path-matching
