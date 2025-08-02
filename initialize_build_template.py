#!/usr/bin/env python3

# Copyright 2025 meator
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Script used to generate a Meson source directory.

This is a pre-configure step which sets up the Google original platform/development
source. Its main purpose is to simplify updating AdbWinApi and the original source. To
do that with this script, edit ANDROID_TOOLS_VERSION.txt and VERSION.txt or override it
using appropriate flags, and (re)generate the source directory using this script.

Updating original source will most likely require updating the build system in
build_template/ too.

See https://github.com/meator/AdbWinApi/blob/main/README.md#deployment-process for more
info about the build process.
"""

import argparse
import os
import pathlib
import platform
import re
import shutil
import string
import sys
import tempfile
import time
import typing
import urllib.request

script_dir = pathlib.Path(__file__).parent
_orig_path = sys.path.copy()
sys.path.insert(1, str(script_dir.absolute()))

import _strip_comments  # noqa: E402
import source_archive_url  # noqa: E402

sys.path = _orig_path
del _orig_path


def _fetch_with_progress(
    url: str, out: typing.BinaryIO, chunk_size: int = 8192, print_delay: float = 1.0
) -> None:
    """Fetch url while showing a simplistic progress indicator.

    Arguments:
        url: Remote file to fetch.
        out: File to write output to.
        chunk_size: Download the file in chunks of chunk_size size.
        print_delay: Print progress every print_delay seconds.
    """
    approximate_size_mib = round(
        source_archive_url.source_archive_approximate_size / 2**20
    )
    fetched_size = 0
    log_delay = time.monotonic()
    with urllib.request.urlopen(url) as response:
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            out.write(chunk)
            fetched_size += len(chunk)

            new_log_delay = time.monotonic()
            if (new_log_delay - log_delay) >= print_delay:
                log_delay = new_log_delay
                progress = round(
                    fetched_size
                    / source_archive_url.source_archive_approximate_size
                    * 100,
                    1,
                )
                progress_str = f"~{progress}"
                fetched_size_mib = round(fetched_size / 2**20)
                print(
                    f"{fetched_size_mib:>4}MiB / ~",
                    approximate_size_mib,
                    f"MiB = {progress_str:>6} %",
                    sep="",
                    file=sys.stderr,
                )


def _universal_symlink(src, dst) -> None:
    try:
        os.symlink(src, dst)
    except OSError as exc:
        # 1314: A required privilege is not held by the client.
        # Windows raises these errors when the script doesn't have
        # sufficient (administrator) priviledges and Developer mode
        # is not enabled (which enables regular users to create
        # symlinks).
        if platform.system() == "Windows" and exc.winerror == 1314:
            shutil.copy(os.path.normpath(os.path.join(os.path.dirname(dst), src)), dst)
        else:
            raise


def _substitute_file(
    filename: pathlib.Path,
    /,
    sourcedir: pathlib.Path,
    destdir: pathlib.Path,
    mapping: typing.Mapping[str, str],
) -> None:
    with open(sourcedir / filename, "r") as file:
        to_substitute = file.read()

    substituted = string.Template(to_substitute).substitute(mapping)

    with open(destdir / filename, "w") as file:
        file.write(substituted)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "destination_directory",
        help="Directory into which build_template/ shall be initialized.",
    )
    parser.add_argument(
        "--android-tools-version",
        help=" ".join(
            (
                "Version of android-tools. If unset, use ANDROID_TOOLS_VERSION.txt",
                "in the same directory this script is located in.",
            )
        ),
    )
    parser.add_argument(
        "--project-version",
        help=" ".join(
            (
                "Version of AdbWinApi project. If unset, use VERSION.txt",
                "in the same directory this script is located in.",
            )
        ),
    )
    args = parser.parse_args()

    # Argument validation and processing.

    dest_dir = pathlib.Path(args.destination_directory)

    if args.android_tools_version:
        # https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
        if not re.match(
            r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
            r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
            r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
            r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$",
            args.android_tools_version,
        ):
            sys.exit("Overriden android_tools_version is not a valid SemVer version!")
        android_tools_version = args.android_tools_version
    else:
        with open(script_dir / "ANDROID_TOOLS_VERSION.txt", "r") as file:
            android_tools_version = _strip_comments.read_file_with_comments(file)

    if args.project_version:
        project_version = args.project_version
    else:
        with open(script_dir / "VERSION.txt", "r") as file:
            project_version = file.read().strip()

    # Fetch source into cache/ if not cached already.

    url = source_archive_url.source_archive_url % {"version": android_tools_version}

    cache_filename = url[url.rfind("/") + 1 :]
    cache_dir = script_dir / "cache"
    cache_path = cache_dir / cache_filename

    # Check for previous failed attempts to download source archive.

    try:
        cachedir_tmp_listing = os.listdir(cache_dir)
    except FileNotFoundError:
        pass
    else:
        for filename in cachedir_tmp_listing:
            if filename.startswith("tmp"):
                print(
                    f"WARNING: Found temporary file '{filename}' in cache directory",
                    f"'{cache_dir}'. Was a previous download abruptly terminated?",
                    "Removing...",
                    file=sys.stderr,
                )
                (cache_dir / filename).unlink()

    # If the source archive is not present, download it.

    if not os.access(cache_path, os.F_OK):
        # The cache is likely empty, let's populate it.
        try:
            tmpcache = tempfile.NamedTemporaryFile(
                dir=cache_dir, prefix="tmp", delete=False
            )
        except FileNotFoundError:
            # cache dir doesn't likely exist, create it and retry
            os.mkdir(cache_dir)
            tmpcache = tempfile.NamedTemporaryFile(
                dir=cache_dir, prefix="tmp", delete=False
            )
        print(f"Fetching {url}...", file=sys.stderr)
        try:
            _fetch_with_progress(url, tmpcache.file)
        except Exception:
            # This script handles leftover temporary files, but we try
            # to clean them up here anyway.
            tmpcache.close()
            os.remove(tmpcache.name)
            raise
        tmpcache.close()
        os.rename(tmpcache.name, cache_path)

    # Copy template to target directory.

    build_template = script_dir / "build_template"

    shutil.copytree(build_template, dest_dir, dirs_exist_ok=True)

    packagefiles_dir = dest_dir / "subprojects" / "packagefiles"

    try:
        _universal_symlink(
            os.path.relpath(cache_path, packagefiles_dir),
            packagefiles_dir / cache_filename,
        )
    except FileExistsError:
        if not os.path.samefile(
            os.path.realpath(packagefiles_dir / cache_filename), cache_path
        ):
            (packagefiles_dir / cache_filename).unlink()
            _universal_symlink(
                os.path.relpath(cache_path, packagefiles_dir),
                packagefiles_dir / cache_filename,
            )

    _substitute_file(
        pathlib.Path("subprojects", "development.wrap"),
        sourcedir=build_template,
        destdir=dest_dir,
        mapping={"version": android_tools_version},
    )
    _substitute_file(
        pathlib.Path("meson.build"),
        sourcedir=build_template,
        destdir=dest_dir,
        mapping={"project_version": project_version},
    )
    _substitute_file(
        pathlib.Path("subprojects", "packagefiles", "patch", "meson.build"),
        sourcedir=build_template,
        destdir=dest_dir,
        mapping={"project_version": project_version, "version": android_tools_version},
    )
