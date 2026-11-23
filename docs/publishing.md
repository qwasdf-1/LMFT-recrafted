# LMFT-recrafted release and marketplace publishing

This is an adaptation of the *workflow* used in
[qwasdf-1/terra-rasa](https://github.com/qwasdf-1/terra-rasa) and
[qwasdf-1/soul-link](https://github.com/qwasdf-1/soul-link), tailored to
LMFT's verified universal Minecraft 26.x artifacts.

**Status:** Publishing automation is being staged. No public marketplace
project is automatically created, and no releases or uploads are made when
this document is committed. Publishing requires a new version tag plus the
corresponding GitHub Actions secrets/variables.

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
4. Only after **both** builds succeed, the release job verifies the expected
   two JARs and SHA-256 checksums, extracts the version changelog, and creates
   a GitHub Release. Alpha/beta/RC tags are prereleases.
5. The release job dispatches the Modrinth and CurseForge workflows on `main`
   with the tagged release name. Those publishers download the *immutable*
   GitHub Release assets and verify SHA-256 hashes before contacting either
   marketplace.
6. Each marketplace publisher creates **one version per loader**, with the
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
