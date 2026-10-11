# Contract changes

The frozen contract is additive-only after Phase 2. Record every change here.

## Template

- Date:
- Change:
- Reason:
- Affected models:
- Compatibility:
- Acceptance tests:

- Date: 2026-10-11
- Change: No frozen contract fields were changed. Upload parsing accepts additive
  organizer aliases and derives a travel matrix from optional location x/y
  coordinates; uploaded/imported metadata stays outside the contract models.
- Reason: Support scenario and schedule uploads without changing contract-v1.
- Affected models: None.
- Compatibility: Existing JSON and CSV scenario payloads remain valid.
- Acceptance tests: `tests/unit/api/test_upload.py` and the round-trip template
  upload coverage.