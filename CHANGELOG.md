# Changelog

## 1.2.0

**First stable LMFT-recrafted release for Minecraft 26.1–26.3.**

This release promotes the tested 26.x functionality introduced in the
1.2.0-alpha.1 preview. No gameplay-facing behavior is intentionally changed
between alpha and stable; the stable release adds a stricter publication gate.

- Recover valid block and item tag entries instead of discarding an entire tag
  when required entries or tag references cannot be resolved.
- Honor optional missing entries and NeoForge's tag-removal semantics.
- Preserve correct recovery after repeated broken, clean and broken-again
  datapack reloads.
- Deliver configurable warning messages correctly to connected operators and
  ordinary players; support public, operator-only and disabled modes.
- Publish one universal Fabric JAR and one universal NeoForge JAR, each built
  against Minecraft 26.3 and tested on 26.1, 26.1.1, 26.1.2, 26.2 and 26.3.
- Require real dedicated-server, cross-version tests of **the actual release
  binaries** on all ten Minecraft/loader combinations before publication.
- License LMFT-recrafted contributions under Apache-2.0 while retaining the
  original CC0 1.0 dedication and crediting original author Blodhgarm.

**Scope:** Java 25; Fabric or NeoForge (install the correct loader JAR).
Minecraft 26.4 and other future releases are not yet supported.
The separately maintained Minecraft 1.21.11 branch is not included in these
26.x release assets. LMFT-recrafted retains the original `lmft` mod ID, so
do not install it alongside upstream LMFT.

**Compatibility note:** Cross-loading with other tag-handler mods or unusual
third-party datapack layering is not exhaustively verified. If there is a
conflict, report the mod list, loader/Minecraft version and relevant logs
at https://github.com/qwasdf-1/LMFT-recrafted/issues.

## 1.2.0-alpha.1

Initial preview of LMFT-recrafted's independently maintained Minecraft 26.x line.

- Preserve valid tag entries when a required entry or tag reference is missing.
- Replace compiler-generated lambda-name tag tracking with scoped tag identifiers.
- Support Minecraft 26.1, 26.1.1, 26.1.2, 26.2 and 26.3.
- Verify one shared Fabric artifact and one shared NeoForge artifact against all five releases.
- Correct operator-only warning filtering and verify player notifications on both loaders.
- Add regression tests for reloads, missing optional references and NeoForge tag removals.
- License LMFT-recrafted contributions under Apache-2.0; preserve original CC0-1.0 text and author credit.

**This is an alpha release candidate.** Review the runtime tests and confirm marketplace project setup before creating the first version tag.
