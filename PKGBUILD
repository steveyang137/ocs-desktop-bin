# Maintainer: syhanjin <syhanjin666@gmail.com>

pkgname=ocs-desktop-bin
pkgver=3.11.1
pkgrel=1
pkgdesc="Desktop manager for browser profiles, extensions and userscripts"
arch=('x86_64')
url="https://github.com/ocsjs/ocs-desktop"
license=('MIT' 'LicenseRef-Google-Chrome')
depends=(
  'alsa-lib' 'at-spi2-core' 'cairo' 'dbus' 'expat' 'glib2' 'glibc'
  'gtk3' 'libcups' 'libgcc' 'libnotify' 'libsecret' 'libstdc++'
  'libx11' 'libxcb' 'libxcomposite' 'libxdamage' 'libxext' 'libxfixes'
  'libxkbcommon' 'libxrandr' 'mesa' 'nspr' 'nss'
  'pango' 'systemd-libs' 'ttf-font' 'xdg-utils' 'hicolor-icon-theme'
)
optdepends=(
  'noto-fonts-cjk: Chinese, Japanese and Korean text rendering'
  'org.freedesktop.secrets: keyring for Electron safe storage and keytar'
)
makedepends=('asar' 'squashfs-tools')
provides=("ocs-desktop=${pkgver}")
conflicts=('ocs-desktop')
options=('!strip' '!debug')

_appimage="ocs-${pkgver}-setup-linux-${arch[0]}.AppImage"
# Match BUILTIN_CHROME_VERSION and BUILTIN_CHROME_SHA256 in the OCS release.
_chromever=137.0.7151.55
_chrome_zip="chrome-${_chromever}-linux64.zip"
source=(
  "https://github.com/ocsjs/ocs-desktop/releases/download/v${pkgver}/${_appimage}"
  "${_chrome_zip}::https://storage.googleapis.com/chrome-for-testing-public/${_chromever}/linux64/chrome-linux64.zip"
  'linux-sandbox.patch'
  'ocs-desktop'
  'ocs-desktop.desktop'
)
noextract=("${_appimage}" "${_chrome_zip}")
sha256sums=(
  '2472646fb0b9fa59593259b939be285fadf059396f8851c406a17ea32315c0cb'
  'ffedd41a261f26e2e60e5d1692e0955c292caffafd15865344d21b845554a3d4'
  '44748fea2268164655da1e17ee5af53818fe466591d2955e8e36f2b1069f4f44'
  'bc96099d9dfe8ab23d97967e3d4980a63d6656df1dc3720f0e482e335a6de270'
  'b429f9110906dc62c65ff9b59b5a28d7cd8c5af4b961b1000f7399dbb907bb64'
)

prepare() {
  local offset
  rm -rf appdir asar-src patched

  # The type-2 runtime reports its SquashFS offset without a FUSE mount.
  chmod u+x "${_appimage}"
  offset=$(./"${_appimage}" --appimage-offset)
  if [[ ! "$offset" =~ ^[1-9][0-9]*$ ]]; then
    printf 'Invalid AppImage SquashFS offset: %s\n' "$offset" >&2
    return 1
  fi
  unsquashfs -no-progress -no-xattrs -o "$offset" -d appdir "${_appimage}"

  # Patch the shipped bundles using exact context. Keep the worker and the
  # native keytar module external to the ASAR, as required by the release.
  asar extract appdir/resources/app.asar asar-src
  patch --directory=asar-src --strip=1 --fuzz=0 < linux-sandbox.patch
  mkdir patched
  asar pack --unpack '*/out/main/script.js' --unpack-dir 'node_modules/keytar' \
    asar-src patched/app.asar
  test -f patched/app.asar.unpacked/out/main/script.js
  test -f patched/app.asar.unpacked/node_modules/keytar/build/Release/keytar.node
}

package() {
  local appdir="$srcdir/appdir"
  local appdst="$pkgdir/usr/lib/ocs-desktop"
  local sharedir="$pkgdir/usr/share"

  install -d "$appdst/resources"
  # Electron uses $ORIGIN. The AppImage launcher and its distro compatibility
  # libraries under usr/lib are unnecessary on Arch.
  cp -a --no-preserve=ownership "$appdir"/{*.pak,*.bin,*.dat,*.so*,*.json,locales} "$appdst/"
  install -m755 "$appdir"/{ocs-desktop,chrome_crashpad_handler} "$appdst/"
  install -m644 "$srcdir/patched/app.asar" "$appdst/resources/app.asar"
  cp -a --no-preserve=ownership "$srcdir/patched/app.asar.unpacked" "$appdst/resources/"

  # Upstream's offline installer reads this archive and puts the runtime
  # browser in Electron's userData directory on first startup.
  install -Dm644 "$srcdir/$_chrome_zip" "$appdst/resources/bin/chrome/chrome.zip"

  install -Dm755 "$srcdir/ocs-desktop" "$pkgdir/usr/bin/ocs-desktop"
  install -Dm644 "$srcdir/ocs-desktop.desktop" "$sharedir/applications/ocs-desktop.desktop"
  install -Dm644 "$appdir/usr/share/icons/hicolor/512x512/apps/ocs-desktop.png" \
    "$sharedir/icons/hicolor/512x512/apps/ocs-desktop.png"
  install -Dm644 -t "$sharedir/licenses/$pkgname" \
    "$appdir"/{LICENSE.electron.txt,LICENSES.chromium.html}
  # The original Chrome notice points to the terms embedded in the browser.
  bsdtar -xOf "$srcdir/$_chrome_zip" chrome-linux64/ABOUT |
    install -m644 /dev/stdin "$sharedir/licenses/$pkgname/chrome-for-testing-ABOUT"
}
