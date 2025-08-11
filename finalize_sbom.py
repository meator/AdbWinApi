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

"""Script used to point SBOM to a release archive.

This script expects the output of generate_sbom.py as input.

See https://github.com/meator/AdbWinApi/blob/main/README.md#software-bill-of-materials
for more info.
"""

# https://cyclonedx.org/docs/1.6/json/

import argparse
import hashlib
import json
from pathlib import Path

_block_size = 4096


def _sha256_hash_file(path: Path) -> str:
    """Return the string sha256sum of provided path."""
    with path.open("rb") as file:
        sha256hash = hashlib.sha256()
        while True:
            block = file.read(_block_size)
            if not block:
                break
            sha256hash.update(block)
        return sha256hash.hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive_path", help="Path to the release archive.")
    parser.add_argument("archive_url", help="URL of the archive")
    parser.add_argument(
        "transform_file",
        help="File to read original SBOM from and to write the modified SBOM into.",
    )
    args = parser.parse_args()

    archive_path = Path(args.archive_path)

    with open(args.transform_file) as input:
        document = json.load(input)

    archive_hash = {
        "alg": "SHA-256",
        "content": _sha256_hash_file(archive_path),
    }

    root = document["metadata"]["component"]
    root["type"] = "file"
    root["name"] = archive_path.name
    root["hashes"] = [archive_hash]
    root["externalReferences"].append(
        {
            "type": "distribution",
            "url": args.archive_url,
            "hashes": [archive_hash],
        }
    )

    with open(args.transform_file, "w") as output:
        json.dump(document, output)
