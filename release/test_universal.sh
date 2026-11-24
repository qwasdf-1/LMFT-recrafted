#!/usr/bin/env bash
# Exercise a previously built (not recompiled) universal release JAR on a
# real standalone Minecraft server. Called by both PR and tagged-release CI.
set -euo pipefail

if [[ "$#" -ne 5 ]]; then
  echo "usage: $0 <fabric|neoforge> <minecraft-version> <pack-format> <neoforge-version-or-dash> <jar-path>" >&2
  exit 2
fi
loader="$1"
mc="$2"
pack="$3"
neo="$4"
jar="$(realpath "$5")"

case "$loader" in
  fabric|neoforge) ;;
  *) echo "Unknown loader $loader" >&2; exit 2 ;;
esac
[[ -f "$jar" ]] || { echo "Missing JAR $jar" >&2; exit 2; }
[[ "$pack" =~ ^[0-9]+$ ]] || { echo "Invalid datapack format: $pack" >&2; exit 2; }
server_dir="$PWD/universal-server"
mkdir -p "$server_dir/mods"
cp "$jar" "$server_dir/mods/"
echo "Testing identical release binary for $loader Minecraft $mc"
sha256sum "$jar"

if [[ "$loader" == fabric ]]; then
  curl --fail --location --retry 3 \
    https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.1.2/fabric-installer-1.1.2.jar \
    -o "$server_dir/fabric-installer.jar"
  java -jar "$server_dir/fabric-installer.jar" server \
    -mcversion "$mc" -loader 0.20.1 -downloadMinecraft -dir "$server_dir"
  test -f "$server_dir/fabric-server-launch.jar"
else
  [[ "$neo" != "-" && -n "$neo" ]] || {
    echo "Missing NeoForge version for $mc" >&2
    exit 2
  }
  curl --fail --location --retry 3 \
    "https://maven.neoforged.net/releases/net/neoforged/neoforge/$neo/neoforge-$neo-installer.jar" \
    -o "$server_dir/neoforge-installer.jar"
  (cd "$server_dir" && java -jar neoforge-installer.jar --installServer)
  test -f "$server_dir/run.sh"
fi

datapack="$server_dir/world/datapacks/lmft-recovery-test"
mkdir -p "$datapack"
cp -R modern/26.3/testdata/. "$datapack/"
python3 - "$datapack/pack.mcmeta" "$pack" "$mc" <<'PY'
import json
import sys
from pathlib import Path
path = Path(sys.argv[1])
format_id = int(sys.argv[2])
mc = sys.argv[3]
data = json.loads(path.read_text(encoding="utf-8"))
data["pack"]["min_format"] = format_id
data["pack"]["max_format"] = format_id
data["pack"]["description"] = f"LMFT stable binary cross-load {mc}"
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
printf 'eula=true\n' > "$server_dir/eula.txt"
printf 'level-name=world\nonline-mode=false\nserver-ip=127.0.0.1\nmax-tick-time=-1\nenable-rcon=true\nrcon.port=25575\nrcon.password=lmft_ci_only\n' \
  > "$server_dir/server.properties"

if [[ "$loader" == fabric ]]; then
  (
    cd "$server_dir"
    timeout --signal=TERM --kill-after=15s 380s \
      java -Xmx2G -jar fabric-server-launch.jar nogui
  ) > "$server_dir/server.log" 2>&1 &
else
  (
    cd "$server_dir"
    timeout --signal=TERM --kill-after=15s 380s bash run.sh nogui
  ) > "$server_dir/server.log" 2>&1 &
fi
server_pid="$!"
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
if ! python3 modern/26.3/tests/server_integration.py \
  --server-log "$server_dir/server.log" \
  --datapack "$datapack" \
  --loader "$loader"; then
  tail -n 200 "$server_dir/server.log"
  exit 1
fi
wait "$server_pid"
grep -q 'Done (' "$server_dir/server.log"
echo "PASS: actual release binary, $loader $mc, reload and recovered-tag assertions"
