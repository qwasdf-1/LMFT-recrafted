# LMFT-recrafted release and marketplace publishing

This is an adaptation of the *workflow* used in
[qwasdf-1/terra-rasa](https://github.com/qwasdf-1/terra-rasa) and
[qwasdf-1/soul-link](https://github.com/qwasdf-1/soul-link), tailored to
LMFT's verified universal Minecraft 26.x artifacts.

**Status:** The end-to-end release automation is operational. The first
alpha `v1.2.0-alpha.1` successfully published both universal JARs to
GitHub, Modrinth and CurseForge on November 24, 2026. A later stable
release still requires a **new** corresponding version tag. Ordinary
commits and pull requests do not publish marketplace versions.

## Release contract

- `release/VERSION`: the release identifier (e.g. `1.2.0-alpha.1`).
- `release/targets.json`: exact game-version list and Minecraft ranges
  compiled into the universal JAR metadata.
- `CHANGELOG.md`: release notes under `## <version>`.
- `release/manifest.py`: validates the tag, jar filenames, target manifest,
  release notes, and SHA-256 hashes, with stdlib-only tests.
- The *only* 26.x marketplace release JARs are
  `lmft-fabric-26.x-<version>+26.x.jar` and
  `lmft-neoforge-26.x-<version>+26.x.jar`.
  Sources JARs are not published as runtime files.
- The two runtime files each declare all five tested Minecraft versions on
  Modrinth and CurseForge. **Do not upload ten redundant copies.**
- The 1.21.11 root Architectury build remains supported through its own
  legacy branch; it is deliberately **not** republished as part of the 26.x
  release pipeline.

## One-time setup

You must establish **LMFT-recrafted's own marketplace project(s)**. Never
reuse the original LMFT author's project IDs unless they explicitly grant
project ownership and upload permissions.

Modrinth: create a project and set its **Source** link to
`https://github.com/qwasdf-1/LMFT-recrafted`. The Actions secret
`MODRINTH_TOKEN` needs PROJECT_READ and VERSION_CREATE capabilities.

**No Modrinth project ID needs to be copied manually.** Set any one of these
Actions variables (whichever you already configured is fine):

- `MODRINTH_PROJECT_ID`: accepts either an actual project ID **or a slug**.
- `MODRINTH_PROJECT_SLUG`: the fork's project slug, such as `lmft-recrafted`.
- `MODRINTH_PROJECT_URL`: full `https://modrinth.com/mod/<slug>` URL.

Before publishing, set the Modrinth project's **License** field to
`Apache-2.0`; the resolver checks it and rejects mismatches rather than
publishing with inconsistent licensing.

The publisher calls Modrinth's `GET /v2/project/{id|slug}` endpoint with the
configured slug/identifier, verifies the returned project's GitHub source
URL against this repository, and then extracts the **canonical project ID**
from `project.id` for its upload payload. If multiple identifiers are
configured they must refer to the same project. The project may need to be
visible through Modrinth's API first; a missing or inaccessible project causes
a safe failure, not publication to a fallback project. When none of the three
identifier variables is present, automatic Modrinth publishing is skipped.

CurseForge: create a new project, generate an uploader API token, set Actions
secret `CURSEFORGE_TOKEN` and Actions variable
`CURSEFORGE_PROJECT_ID` to the new project's **numeric ID**. Never use the
existing original LMFT CurseForge project ID. If game-version IDs cannot be
resolved automatically, set `CURSEFORGE_GAME_VERSIONS` to a JSON object
mapping each supported Minecraft version to its official CurseForge numeric
game version ID, for example `{"26.1":[12345],"26.2":[23456]}`.
Optional `CURSEFORGE_ENVIRONMENT` can be `client`, `server`, or `both`
(default `both`). If the project ID variable is absent, CurseForge
publishing is skipped.

**Do not use the same project IDs as Terra Rasa, Soul Link or upstream LMFT.**
Marketplace project metadata (name, description, license, galleries and
ownership) is managed on the marketplace itself, not by this pipeline.

## Workflow

1. Update `release/VERSION`, `CHANGELOG.md`, and any changed target ranges.
   Verify the GitHub CI and universal cross-load tests on `main`.
2. Push an annotated `v<version>` tag pointing to a commit already on
   `main` (the release workflow rejects unrelated or mismatched tags).
3. `.github/workflows/release.yml` builds both universal 26.x JARs using
   Java 25 and the correct Gradle version for each loader.
4. Before publication, the release gate downloads those exact compiled
   JARs and installs them unchanged on five standalone Minecraft versions
   **per loader** (ten servers). Every test asserts recovered tag membership,
   repeated broken/clean reloads and NeoForge removal behavior.
5. Only after **both** builds **and all ten binary cross-loading checks**
   succeed, the release job verifies both JARs, writes SHA-256 checksums,
   extracts the version changelog, and creates a GitHub Release. Alpha/beta/RC tags are prereleases.
6. The release job dispatches the Modrinth and CurseForge workflows on `main`
   with the tagged release name. Those publishers download the *immutable*
   GitHub Release assets and verify SHA-256 hashes before contacting either
   marketplace.
7. Each marketplace publisher creates **one version per loader**, with the
   complete tested Minecraft 26.x target list. Use Actions **Run workflow**
   with an existing release tag to retry a failed marketplace upload.

Modrinth checks whether a matching version already exists before upload:
a matching version and file hash are accepted; divergent metadata or bytes
fail rather than overwriting. CurseForge's upload endpoint reports duplicate
files differently; the workflow treats explicit duplicate errors as skipped
rather than silently uploading more files. Verify CurseForge's listing after
an interrupted upload.

## Licensing

The project has finalized **Apache-2.0 for LMFT-recrafted contributions**
and retained the original upstream **CC0-1.0** dedication separately:
`LICENSE` is Apache License 2.0, `LICENSES/CC0-1.0.txt` is the unmodified
upstream license, and `NOTICE` credits original author **Blodhgarm** and
links the original source. Built JARs include all three documents under
`META-INF`. Update the license on each new Modrinth and CurseForge project
to **Apache License 2.0** before its first public upload; retain the
upstream CC0 notice in the source and released JARs. This is a fork, not a
relicensing of the original author's upstream project.

## Dry-run checks

```bash
python3 -m unittest discover -s release/tests -v
python3 release/manifest.py version
python3 release/manifest.py notes
python3 release/manifest.py games
```


## Read-only credentials verification

After merging, open GitHub Actions and run **Verify marketplace credentials
(no uploads)**. This checks the already configured variables and secrets
without creating a GitHub Release, pushing a version tag, or uploading files.

For Modrinth it resolves the configured slug (including a slug placed in
`MODRINTH_PROJECT_ID`) to the canonical project ID, validates the project's
GitHub source link, and displays the resolved ID in the workflow summary.
For CurseForge it checks the token against the game-version API and verifies
that all five Minecraft versions can be tagged for each loader; this does
not conclusively validate permission to upload to a particular project.

A project still awaiting Modrinth API visibility may temporarily fail that
read-only check; the publisher will likewise fail safely rather than
upload to an unintended project.


### Duplicate CurseForge Minecraft version names

CurseForge can return several numeric IDs with the same version label,
including `26.1`, in distinct version categories. The resolver fetches
**both** `/api/game/versions` and `/api/game/version-types` and uses the
`gameVersionTypeID` to select the matching **Minecraft release**
category, rather than guessing from the displayed version name or
choosing the first result. A Minecraft 26.1 category also covers 26.1.x
hotfixes. If the category data remains genuinely ambiguous, publishing
fails closed and prints the candidate IDs and category names.

`CURSEFORGE_GAME_VERSIONS` remains an optional, manually verified
override for unusual API metadata; it should not be needed simply because
another category uses the same Minecraft version name.


### Numeric-only CurseForge release categories

CurseForge's Minecraft-scoped `/api/game/version-types` endpoint may name a
Minecraft release family simply `26.2`, rather than `Minecraft 26.2`.
The version resolver recognizes either form. In the reported 26.2 case,
version ID `16498` belongs to type `86297` (category name `26.2`),
while a second record `16500` points to type ID `1`, absent from the
version-type table. The resolver selects `16498` from the explicitly
matching version family and ignores the unknown category.

Unknown or conflicting categories still produce an error instead of a
guess. This behavior is covered by release resolver unit tests.

## Stable release acceptance criteria

A normal `vMAJOR.MINOR.PATCH` version (no `-alpha`, `-beta`, `-rc`)
is published as a **release** on Modrinth and CurseForge, not a prerelease.

Promote a tested preview to stable when all of the following hold:

- The scope and supported Minecraft versions are explicitly documented,
  with no claim of untested future releases or universal third-party mod
  compatibility.
- Dedicated-server tests are green for Fabric and NeoForge on all five
  advertised Minecraft versions, and multiplayer join/reload notification
  behavior is verified on Minecraft 26.3 on both loaders.
- The **two actual release artifacts**, not separately rebuilt version-pinned
  jars, pass recovery, reload and NeoForge-removal checks in ten isolated
  standalone Minecraft servers, and their metadata/embedded license notices
  are verified.
- Known release-blocking bugs are resolved, with no regression from the
  preceding preview; marketplace credentials and project metadata are valid.
- The release changelog accurately describes changes and known limitations;
  the version tag points to a commit merged into `main`.

This release gate verifies vanilla/loader interoperability, **not** every
possible third-party mod combination. Alpha is not a guarantee of stable
field experience; continue monitoring and issue-fix releases after launch.
