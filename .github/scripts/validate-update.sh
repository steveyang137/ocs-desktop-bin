#!/usr/bin/env bash
set -euo pipefail

pacman -Syu --noconfirm --needed asar python squashfs-tools
# Use a different UID from the runner so the build cannot modify /result.
useradd --create-home --uid 12001 builder
install -d -o builder /tmp/recipe
install -m644 -o builder -t /tmp/recipe /checkout/{PKGBUILD,linux-sandbox.patch,ocs-desktop,ocs-desktop.desktop}
cd /tmp/recipe
script=/checkout/.github/scripts/update-package.py

args=()
if [[ "${VALIDATE_CURRENT:-false}" == true ]]; then
  args+=(--validate-current)
fi
version=$(runuser -u builder -- python "$script" "${args[@]}")
if [[ -z "$version" ]]; then
  exit 0
fi

runuser -u builder -- bash -n PKGBUILD
runuser -u builder -- bash -c 'makepkg --printsrcinfo > .SRCINFO'
if ! cmp -s /checkout/PKGBUILD PKGBUILD; then
  # Snapshot before building the release artifact. The publisher only runs
  # once the container exits successfully.
  install -m644 PKGBUILD .SRCINFO /result/
  printf '%s\n' "$version" > /result/version
else
  diff -u /checkout/.SRCINFO .SRCINFO
fi
runuser -u builder -- makepkg --verifysource
# The binary package build checks the AppImage extraction and exact patch
# context. Its runtime dependencies are unnecessary for this build check.
runuser -u builder -- makepkg --nodeps --cleanbuild
runuser -u builder -- python "$script" --check-layout
