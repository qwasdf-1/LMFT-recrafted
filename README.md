# Load My F***ing Tags

Load My F***ing Tags is a small QOL Mod that prevents Minecraft from failing to Load a whole tag if one or more Entries could not be found. This is useful for when Mod Devs or DataPack Devs who may have messed up with there Tags and it causes Minecraft Core functions to take a dive for the worst causing you massive Game Play Headaches.


## LMFT-recrafted

This repository is an independently maintained continuation of [the original LMFT](https://github.com/Dragon-Seeker/LoadMyFingTags). It retains the original `lmft` mod identifier. Credits to the original author, Blodhgarm.

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

**Download:** [LMFT-recrafted releases](https://github.com/qwasdf-1/LMFT-recrafted/releases).
Install the Fabric JAR with Fabric or the NeoForge JAR with NeoForge,
on the server; clients do not need to install LMFT-recrafted.
Do not install the original LMFT and LMFT-recrafted together: both use
the `lmft` mod ID. Minecraft 26.4 and later versions are not yet covered.

### Publishing

Releases for Minecraft 26.x are built from version tags on `main`.
The workflow produces **one Fabric JAR and one NeoForge JAR**, runs real
standalone-server recovery/reload checks using the **exact two compiled
binaries** on all five supported Minecraft versions per loader, generates
SHA-256 checksums, and publishes to GitHub, Modrinth and CurseForge only
when the release gate succeeds.

See [automated publishing setup](docs/publishing.md) for the one-time secrets,
project IDs, release process and retry rules. Development and PR builds never
upload to marketplaces.

### License

**LMFT-recrafted contributions and modifications are licensed under Apache-2.0**
(see [LICENSE](LICENSE)). The original Load My F***ing Tags code and resources
were released under **CC0-1.0 Universal** and retain their original dedication
([LICENSES/CC0-1.0.txt](LICENSES/CC0-1.0.txt)).

We credit **Blodhgarm**, the original author, and preserve the upstream source
link in [NOTICE](NOTICE). This independent continuation is not endorsed by the
original author. Both license texts and the notice are bundled with releases.
