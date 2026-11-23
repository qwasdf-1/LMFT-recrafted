# Changelog

## 1.2.0-alpha.1

Initial preview of LMFT-recrafted's independently maintained Minecraft 26.x line.

- Preserve valid tag entries when a required entry or tag reference is missing.
- Replace compiler-generated lambda-name tag tracking with scoped tag identifiers.
- Support Minecraft 26.1, 26.1.1, 26.1.2, 26.2 and 26.3.
- Verify one shared Fabric artifact and one shared NeoForge artifact against all five releases.
- Correct operator-only warning filtering and verify player notifications on both loaders.
- Add regression tests for reloads, missing optional references and NeoForge tag removals.

**This is an alpha release candidate.** Review the runtime tests and confirm marketplace project setup before creating the first version tag.
