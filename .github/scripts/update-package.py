"""Prepare and check a version bump for the current Arch package recipe."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from zipfile import BadZipFile, ZipFile

UPSTREAM = "https://github.com/ocsjs/ocs-desktop"
RELEASE_API = "https://api.github.com/repos/ocsjs/ocs-desktop/releases/latest"
PKGBUILD = Path("PKGBUILD")
VERSION = r"[0-9]+\.[0-9]+\.[0-9]+"
CHROME_VERSION = VERSION + r"\.[0-9]+"
SHA256 = r"[a-f0-9]{64}"


def fetch(url):
    with urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8")


def match_once(pattern, text, description):
    matches = list(re.finditer(pattern, text, re.MULTILINE))
    if len(matches) != 1:
        raise ValueError(f"expected one {description}, found {len(matches)}")
    return matches[0]


def chrome_lock(tag):
    source = fetch(
        f"https://raw.githubusercontent.com/ocsjs/ocs-desktop/{tag}"
        "/packages/common/src/utils/chrome.source.ts"
    )
    version = match_once(
        rf"""^export const BUILTIN_CHROME_VERSION = ['"]({CHROME_VERSION})['"];[ \t]*$""",
        source,
        "Chrome version in the upstream source",
    )[1]
    checksums = match_once(
        r"^export const BUILTIN_CHROME_SHA256[^\n]*= \{([^}]+)\};",
        source,
        "Chrome checksum table in the upstream source",
    )[1]
    digest = match_once(
        rf"""^[ \t]*linux64: ['"]({SHA256})['"],?[ \t]*$""",
        checksums,
        "linux64 Chrome checksum in the upstream source",
    )[1]
    return version, digest


def prepare(include_current):
    recipe = PKGBUILD.read_text()
    current = match_once(rf"^pkgver=({VERSION})$", recipe, "pkgver")[1]
    release = json.loads(fetch(RELEASE_API))
    if release.get("draft") is not False or release.get("prerelease") is not False:
        raise ValueError("GitHub's latest release endpoint did not return a stable release")

    tag = release["tag_name"]
    latest = re.fullmatch(rf"v({VERSION})", tag)
    if not latest:
        raise ValueError(f"unsupported upstream release tag {tag!r}")
    version = latest[1]
    order = int(subprocess.check_output(["vercmp", version, current], text=True))
    if order < 0 or (order == 0 and not include_current):
        print(f"Upstream: {version}. Package: {current}. No update.", file=sys.stderr)
        return

    image = f"ocs-{version}-setup-linux-x86_64.AppImage"
    assets = [asset for asset in release["assets"] if asset["name"] == image]
    if len(assets) != 1:
        raise ValueError(f"expected one x86_64 asset named {image}, found {len(assets)}")
    asset = assets[0]
    if asset["browser_download_url"] != f"{UPSTREAM}/releases/download/{tag}/{image}":
        raise ValueError("unexpected AppImage download URL")
    digest = re.fullmatch(rf"sha256:({SHA256})", asset.get("digest") or "")
    if not digest:
        raise ValueError("official AppImage SHA-256 is unavailable")

    chrome_version, chrome_digest = chrome_lock(tag)
    old_chrome = match_once(rf"^_chromever=({CHROME_VERSION})$", recipe, "_chromever")
    checksums = match_once(
        r"^sha256sums=\(\n((?:  '[a-f0-9]{64}'\n){5})\)$",
        recipe,
        "five source checksums",
    )
    old_digests = re.findall(SHA256, checksums[1])
    if order == 0:
        if (old_chrome[1], *old_digests[:2]) != (chrome_version, digest[1], chrome_digest):
            raise ValueError("current PKGBUILD differs from the upstream release or Chrome lock")
    else:
        release_number = match_once(r"^pkgrel=[0-9]+(?:\.[0-9]+)?$", recipe, "pkgrel")
        recipe = recipe.replace(checksums[0], "sha256sums=(\n" + "".join(
            f"  '{value}'\n" for value in [digest[1], chrome_digest, *old_digests[2:]]
        ) + ")")
        recipe = recipe.replace(old_chrome[0], f"_chromever={chrome_version}")
        recipe = recipe.replace(release_number[0], "pkgrel=1")
        recipe = recipe.replace(f"pkgver={current}\n", f"pkgver={version}\n", 1)
        PKGBUILD.write_text(recipe)

    print(version)


def check_layout():
    recipe = PKGBUILD.read_text()
    chrome = match_once(rf"^_chromever=({CHROME_VERSION})$", recipe, "_chromever")[1]
    checksums = match_once(
        r"^sha256sums=\(\n((?:  '[a-f0-9]{64}'\n){5})\)$",
        recipe,
        "five source checksums",
    )
    chrome_digest = re.findall(SHA256, checksums[1])[1]
    bundle = Path("src/asar-src/out/main/index.js").read_text()
    bundled_version = match_once(
        rf'^const BUILTIN_CHROME_VERSION = "({CHROME_VERSION})";$',
        bundle,
        "Chrome version in the AppImage bundle",
    )[1]
    bundled_digest = match_once(
        rf'^  linux64: "({SHA256})",?$',
        bundle,
        "Chrome checksum in the AppImage bundle",
    )[1]
    if (bundled_version, bundled_digest) != (chrome, chrome_digest):
        raise ValueError("AppImage and upstream source disagree on the Chrome lock")

    with ZipFile(f"chrome-{chrome}-linux64.zip") as archive:
        for name in ("chrome", "chrome_crashpad_handler"):
            entry = archive.getinfo(f"chrome-linux64/{name}")
            if entry.file_size == 0 or not (entry.external_attr >> 16) & 0o100:
                raise ValueError(f"Chrome archive member {name} is empty or cannot be executed")
        archive.getinfo("chrome-linux64/ABOUT")
    print(f"Verified AppImage and Chrome {chrome} resource layout.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--validate-current", action="store_true")
    mode.add_argument("--check-layout", action="store_true")
    args = parser.parse_args()
    try:
        if args.check_layout:
            check_layout()
        else:
            prepare(args.validate_current)
    except (BadZipFile, KeyError, OSError, TypeError, URLError, ValueError,
            subprocess.CalledProcessError) as exc:
        sys.exit(f"OCS Desktop update failed: {exc}")


if __name__ == "__main__":
    main()
