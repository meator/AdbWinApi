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

import argparse
import os
import pathlib
import re
import shutil
import string
import sys

script_dir = pathlib.Path(__file__).parent
sys.path.insert(1, script_dir.absolute())

import _strip_comments

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "destination_directory",
        help="Directory into which wrap_build_template/ shall be initialized.",
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
            sys.exit("Overriden --android-tools-version is not a valid SemVer version!")
        android_tools_version = args.android_tools_version
    else:
        with open(script_dir / "ANDROID_TOOLS_VERSION.txt", "r") as file:
            android_tools_version = _strip_comments.read_file_with_comments(file)

    if args.project_version:
        project_version = args.project_version
    else:
        with open(script_dir / "VERSION.txt", "r") as file:
            project_version = file.read().strip()

    # Process substitutions in input wrap_build_template/meson.build file

    with open(script_dir / "wrap_build_template" / "meson.build", "r") as file:
        meson_build_contents = string.Template(file.read()).substitute(
            project_version=project_version, library_version=android_tools_version
        )

    # Write the result into destination directory.

    try:
        with open(dest_dir / "meson.build", "w") as file:
            file.write(meson_build_contents)
    except FileNotFoundError:
        os.mkdir(dest_dir)
        with open(dest_dir / "meson.build", "w") as file:
            file.write(meson_build_contents)

    shutil.copytree(
        script_dir / "wrap_build_template",
        dest_dir,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("meson.build"),
    )
