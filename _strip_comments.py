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
import sys
import typing

def read_file_with_comments(to_read: typing.TextIO) -> str:
    """Read a file while ignoring # comments.

    This function doesn't expect to receive multiline files (excluding the comments).
    """
    result = ""
    for line in to_read:
        if len(line) >= 1 and line[0] == "#":
            continue
        result += line
    return result.strip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        help="File to print without comments to stdout. If unset, use stdin.",
        nargs="?",
    )
    args = parser.parse_args()

    if args.file is not None:
        with open(args.file, "r") as file:
            print(read_file_with_comments(file))
    else:
        print(read_file_with_comments(sys.stdin))
