# Load My F***ing Tags

Load My F***ing Tags is a small QOL Mod that prevents Minecraft from failing to Load a whole tag if one or more Entries could not be found. This is useful for when Mod Devs or DataPack Devs who may have messed up with there Tags and it causes Minecraft Core functions to take a dive for the worst causing you massive Game Play Headaches.


## LMFT-recrafted

This repository is an independently maintained continuation of [the original LMFT](https://github.com/Dragon-Seeker/LoadMyFingTags). It retains the original `lmft` mod identifier and credits the original author, Blodhgarm.

### Validated Minecraft versions

| Minecraft | Fabric | NeoForge |
|---|---|---|
| 1.21.11 | Legacy build | Legacy build |
| 26.1 | Universal 26.x build | Universal 26.x build |
| 26.1.1 | Universal 26.x build | Universal 26.x build |
| 26.1.2 | Universal 26.x build | Universal 26.x build |
| 26.2 | Universal 26.x build | Universal 26.x build |
| 26.3 | Universal 26.x build | Universal 26.x build |

Minecraft 26.x uses **Java 25** and the independent builds under `modern/26.3/`. The same compiled universal Fabric JAR and the same compiled universal NeoForge JAR have each been tested on all five stable 26.x versions. Separate loader JARs are still required. The root Architectury build remains the 1.21.11 implementation; it is not a universal 26.x artifact.

### Builds and tests

- `modern/26.3/README.md`: Gradle commands for individual Minecraft versions and build setup.
- `docs/26.x-jars-and-compatibility-audit.md`: single-JAR runtime evidence and limitations.
- `docs/26.x-verification-checklist.md`: automated game-level verification and remaining release checks.
- `.github/workflows/modern-26.3.yml` and `modern-26.x-compatibility.yml`: dedicated-server tag membership, reload, missing-entry and NeoForge removal tests.
- `.github/workflows/multiplayer-notifications.yml`: two actual connected players, with operator-only, public, disabled and JVM-suppressed warning delivery checks.

These are tested development artifacts; check GitHub Releases for published builds. Do not install the original LMFT and LMFT-recrafted together: both use the `lmft` mod ID.
