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
import pathlib
import string
import hashlib

_buffer_size = 8192

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_release_archive",
        help=" ".join(
            (
                "Input .tar.gz file containing prebuilt libraries. Its",
                "sha256sum will be computed.",
            )
        ),
    )
    parser.add_argument(
        "output_file",
        help="File into which should the processed version of AdbWinApi.wrap.in be put",
    )
    parser.add_argument(
        "project_version",
        nargs="?",
        help=" ".join(
            (
                "Version of AdbWinApi project. If unset, use VERSION.txt",
                "in the same directory this script is located in.",
            )
        ),
    )
    args = parser.parse_args()

    # Argument validation and processing.

    script_dir = pathlib.Path(__file__).parent

    if args.project_version:
        project_version = args.project_version
    else:
        with open(script_dir / "VERSION.txt", "r") as file:
            project_version = file.read().strip()

    sha256sum = hashlib.sha256(usedforsecurity=False)
    with open(args.input_release_archive, "rb") as file:
        while True:
            chunk = file.read(_buffer_size)
            if not chunk:
                break
            sha256sum.update(chunk)

    with open(script_dir / "AdbWinApi.wrap.in", "r") as file:
        wrap_file_contents = string.Template(file.read()).substitute(
            version=project_version,
            sha256sum=sha256sum.hexdigest(),
        )

    # Write the result into destination directory.

    with open(args.output_file, "w") as file:
        file.write(wrap_file_contents)
