#!/usr/bin/env bash
set -euo pipefail
#
# vita-build.sh — Local PS Vita build, validate & deploy automation
#
# Usage:
#   ./scripts/vita-build.sh              # Build + validate (US)
#   ./scripts/vita-build.sh jp           # Build + validate (JP)
#   ./scripts/vita-build.sh us --deploy  # Build + validate + FTP deploy
#
# Optional env vars:
#   VERSION=us          Game version (us/jp/eu/sh)
#   VITA_IP=192.168.1.X  FTP deploy target (set to enable --deploy)
#   JOBS=4              Parallel jobs (default: nproc)
#

VERSION="${VERSION:-${1:-us}}"
JOBS="${JOBS:-$(nproc)}"
DEPLOY="${DEPLOY:-false}"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Parse args
for arg in "$@"; do
  case "$arg" in
    --deploy|--upload) DEPLOY=true ;;
    us|jp|eu|sh) VERSION="$arg" ;;
  esac
done

cd "$SCRIPT_DIR"

echo "══════════════════════════════════════════════"
echo "  SM64DS Remastered — Vita Build v$VERSION"
echo "══════════════════════════════════════════════"
echo ""

# ── Step 1: Verify dependencies ──────────────────
echo "▸ Checking toolchain..."
command -v arm-vita-eabi-gcc >/dev/null 2>&1 || {
  echo "✗ arm-vita-eabi-gcc not found! Is VITASDK installed?"
  echo "  export VITASDK=/usr/local/vitasdk"
  exit 1
}

# ── Step 2: Verify baserom ───────────────────────
echo "▸ Checking baserom.$VERSION.z64..."
if [ ! -f "baserom.$VERSION.z64" ]; then
  echo "✗ baserom.$VERSION.z64 not found!"
  echo "  Place the original SM64DS ROM at: baserom.$VERSION.z64"
  exit 1
fi
echo "  ✓ Found ($(du -h "baserom.$VERSION.z64" | cut -f1))"

# ── Step 3: Clean previous build (optional) ──────
if [ -d "build/${VERSION}_vita" ]; then
  echo "▸ Cleaning previous build..."
  make TARGET_VITA=1 VERSION="$VERSION" clean 2>/dev/null || true
fi

# ── Step 4: Build VPK ───────────────────────────
echo ""
echo "▸ Building VPK (${JOBS} parallel jobs)..."
START_TIME=$SECONDS
make TARGET_VITA=1 VERSION="$VERSION" -j"$JOBS" vpk
BUILD_TIME=$((SECONDS - START_TIME))

VPK=$(ls "build/${VERSION}_vita/"*.vpk 2>/dev/null || true)
if [ -z "$VPK" ]; then
  echo "✗ Build completed but no VPK found!"
  exit 1
fi

echo ""
echo "▸ Build finished in ${BUILD_TIME}s"
echo "  VPK: $VPK ($(du -h "$VPK" | cut -f1))"

# ── Step 5: Validate VPK ────────────────────────
echo ""
echo "══════════ VPK Validation ═══════════════════"
FAILED=0

# 5a. ZIP integrity
if unzip -t "$VPK" > /dev/null 2>&1; then
  echo "  ✓ Valid ZIP archive"
else
  echo "  ✗ Corrupt ZIP archive"
  FAILED=1
fi

# 5b. Required files
for req in "eboot.bin" "param.sfo" "sce_sys/icon0.png"; do
  if unzip -l "$VPK" | grep -q "$req"; then
    echo "  ✓ Contains $req"
  else
    echo "  ✗ Missing $req"
    FAILED=1
  fi
done

# 5c. SCE magic (eboot.bin must start with SCE\0)
EBOOT_MAGIC=$(unzip -p "$VPK" eboot.bin | xxd -l 4 -p 2>/dev/null || echo "missing")
if [ "$EBOOT_MAGIC" = "53434500" ]; then
  echo "  ✓ eboot.bin SCE magic valid"
else
  echo "  ✗ eboot.bin bad magic (got: $EBOOT_MAGIC, expected: 53434500)"
  FAILED=1
fi

# 5d. No forbidden sce_sys/package/ files
if unzip -l "$VPK" | grep -q "sce_sys/package/"; then
  echo "  ✗ Contains sce_sys/package/ — will cause 0x80870005 install failure!"
  FAILED=1
else
  echo "  ✓ No forbidden sce_sys/package/ files"
fi

# 5e. PNG size check
for png in $(unzip -l "$VPK" | grep -oP 'sce_sys/.*\.png'); do
  SIZE=$(unzip -l "$VPK" | grep "$png" | awk '{print $1}')
  if [ "${SIZE:-0}" -gt 430080 ] 2>/dev/null; then
    echo "  ✗ $png is ${SIZE}B (> 420KB) — may crash install"
    FAILED=1
  else
    echo "  ✓ $png ($(numfmt --to=iec "${SIZE:-0}" 2>/dev/null || echo "${SIZE}B"))"
  fi
done

echo "══════════════════════════════════════════════"
if [ "$FAILED" -eq 1 ]; then
  echo "  ❌ VALIDATION FAILED"
  exit 1
else
  echo "  ✅ VPK validation passed"
fi

# ── Step 6: FTP Deploy (optional) ────────────────
if [ "$DEPLOY" = true ]; then
  VITA_IP="${VITA_IP:-}"
  if [ -z "$VITA_IP" ]; then
    echo ""
    echo "▸ --deploy requested but VITA_IP not set."
    echo "  export VITA_IP=192.168.1.X"
    echo "  Skipping deploy."
  else
    echo ""
    echo "▸ Deploying VPK to Vita at $VITA_IP:1337..."
    echo "  (VitaShell must be running with FTP enabled)"
    if curl -T "$VPK" "ftp://$VITA_IP:1337/ux0:/download/" 2>&1; then
      echo "  ✓ VPK uploaded to ux0:/download/"
      echo "  Install via VitaShell: navigate to ux0:/download/ and install"
    else
      echo "  ✗ FTP upload failed. Check VITA_IP and VitaShell FTP status."
    fi
  fi
fi

# ── Summary ──────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════"
echo "  ✅ Build complete"
echo "  File: $VPK"
echo "  Size: $(du -h "$VPK" | cut -f1)"
echo "  Time: ${BUILD_TIME}s"
echo "══════════════════════════════════════════════"
