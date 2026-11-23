# LMFT modern Minecraft 26.x implementation (Fabric and NeoForge)

**Status: both loaders passed real-server membership, reload and NeoForge removal tests on 26.1, 26.1.1, 26.1.2, 26.2 and 26.3.**
The existing Minecraft 1.21.11 Architectury build at repository root is unchanged.

## Project layout

- `common/`: shared tag recovery, JSON configuration, chat messages and
  Minecraft 26.3 mixins.
- `fabric/`: standalone Fabric Loom 1.19 build, Fabric Loader 0.20.1.
- `neoforge/`: standalone ModDevGradle 2.0.148 build, NeoForge 26.3.0.115.
- `tests/`: plain Java 21+ tests for the loader-independent recovery logic.
- `testdata/`: Minecraft 26.3 datapack that deliberately contains missing
  required references and one missing optional entry.

These builds are intentionally separate Gradle roots: the legacy project's
Gradle 8.11/Java 21/Architectury toolchain is not compatible with the modern
26.3 Java 25 toolchain. No Fabric API dependency is introduced.

## Build

Install **JDK 25** and **Gradle 9.8.2** for Fabric. From this repository:

```bash
gradle -p modern/26.3/fabric build
```

For NeoForge, use **JDK 25** and **Gradle 9.2.1** (official MDK version):

```bash
gradle -p modern/26.3/neoforge build
```

The repository's root `./gradlew` is **not** suitable for either modern build.

## Unit smoke test (Java 21+)

```bash
tmpdir=$(mktemp -d)
javac -d "$tmpdir" modern/26.3/common/src/main/java/io/wispforest/lmft/TagRecovery.java modern/26.3/tests/TagRecoveryTest.java
java -cp "$tmpdir" io.wispforest.lmft.TagRecoveryTest
rm -rf "$tmpdir"
```

## Functional test

1. Run a dedicated Minecraft **26.3** Fabric/NeoForge server with its LMFT
   JAR (test each loader separately).
2. Copy `modern/26.3/testdata` into a new world as
   `world/datapacks/lmft-recovery-test` (so `pack.mcmeta` is its root).
3. Start/reload the world and inspect the logs. The
   `lmft_test:recovery` and `lmft_test:missing_tag_reference` tags
   should retain `minecraft:stone` and log their missing references with
   the corresponding tag ID.
4. `lmft_test:optional` must not produce a missing-entry warning.
5. Check the warning notification after joining and `/reload` with
   `showToOnlyPrivileged` both false and true, as operator and nonoperator.
6. Check NeoForge tag-removal semantics and repeated reloads independently.

**Important:** success requires functional verification; a successful build
alone does not establish correct Mixin application or tag retention.
The recovery Mixin uses `require = 1` for both hook points, so a changed
Minecraft method should fail fast rather than silently disabling protection.

The tag-ID hook wraps the callback supplied to
`DependencySorter.orderByDependencies(BiConsumer)`, avoiding the fragile
compiler-generated `lambda$build$N` name.

Configuration remains `config/lmft.json`, with keys
`disableIngameError` and `showToOnlyPrivileged`; JVM property
`-Dlmft.disable_error_output=true` suppresses the chat warning.

For design evidence and known risks, see
`docs/26.3-tagloader-hook-investigation.md`.

## Other 26.x versions

The same Java sources and build definitions accept `-Pminecraft_version=<version>` to
recompile for a specific stable 26.x release. For NeoForge, also provide
`-Pneo_version=<matching NeoForge build>`. Supply `-Pmod_version=<mod release>`
when producing an artifact for that version. The Fabric and NeoForge metadata
is expanded to require exactly the selected Minecraft release, rather than
advertising an untested range.

The `modern-26.x-compatibility.yml` workflow builds and runs Minecraft 26.1,
26.1.1, 26.1.2 and 26.2 with version-matched NeoForge dependencies and datapack
formats. Together with the 26.3 CI, all ten configurations passed real server
tag-membership and repeated-reload tests on November 23, 2026.
The folder name `modern/26.3` is historical; it hosts the shared 26.x source.

## Opt-in single-JAR 26.x artifacts

Standalone-server cross-loading tests installed *one compiled JAR* per loader
on **all five** stable 26.x releases and passed full recovery/reload tests.
See the experimental Fabric run (https://github.com/qwasdf-1/LMFT-recrafted/actions/runs/45262108847)
and NeoForge run (https://github.com/qwasdf-1/LMFT-recrafted/actions/runs/45262555701).

The normal build remains version-pinned. To produce universal-range release
candidates directly through Gradle, use JDK 25 and the appropriate Gradle version:

```bash
gradle -p modern/26.3/fabric build \\
  -Pminecraft_range='>=26.1 <26.4' \\
  -Pmod_version='1.2.0-alpha.1+26.x'

gradle -p modern/26.3/neoforge build \\
  -Pminecraft_range='[26.1,26.4)' \\
  -Pneoforge_range='[26.1.0.19-beta,)' \\
  -Pmod_version='1.2.0-alpha.1+26.x'
```

Both compile against Minecraft 26.3 and produce separately named Fabric or
NeoForge `26.x` artifacts. No extra Fabric API dependency is required.
The validation workflows still retain exact-version builds as a regression
control. Widening version metadata outside the tested set requires new server
tests; 26.4 is not included.

Before publishing a full release, manually validate connected-player chat
notifications and operator-only filtering as described in
`docs/26.x-verification-checklist.md`. The headless server tests cannot
verify actual client chat delivery.
