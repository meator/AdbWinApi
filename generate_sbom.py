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

"""Custom script used to generated SBOM for AdbWinApi.

This script depends on the Python standard library only.

See https://github.com/meator/AdbWinApi/blob/main/README.md#deployment-process for more
info about the SBOM generation process.
"""

# #######################################################
# #               WARNING WARNING WARNING               #
# #               =======================               #
# # If you edit this file, make sure that you rerun     #
# # initialize_build_template.py, otherise your changes #
# # will not take effect!                               #
# #######################################################
#
# You can disregard the message above if you are using a -src
# release archive, as it does not include initialize_build_template.py.

# This script is tailored for the current release process of meator/AdbWinApi. If you
# want to do any of the following:
# - fork this project and host/build it outside of GitHub
# - use dependencies (or components as CycloneDX calls it) from other sources than
#   the ones used in the original GitHub Action
# - substantially modify the build environment used
#
# You will have to modify this script. A failure to do so will lead to discrepencies in
# the generated SBOM.
#
# If you want to fork this project on GitHub and host built release artifacts on
# GitHub, you shouldn't need to modify this script, you only need to provide the
# correct arguments to it (i.e. modify
# build_template/subprojects/packagefiles/patch/meson.build).

# https://cyclonedx.org/docs/1.6/json/

import argparse
import configparser
import datetime
import hashlib
import itertools
import json
import platform
import shutil
import string
import subprocess
import sys
import typing
import uuid
from pathlib import Path

_block_size = 4096

# string.Template().get_identifiers() requires 3.11
if sys.version_info[0] != 3 or sys.version_info[1] < 11:
    sys.exit("This script requires Python version >=3.11")

script_dir = Path(__file__).parent
_orig_path = sys.path.copy()
sys.path.insert(1, str(script_dir.absolute()))

import source_archive_url  # noqa: E402

sys.path = _orig_path
del _orig_path

url_func = typing.Callable[[Path], str] | None


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


def _git_get_current_commit_hash() -> str | None:
    """Try to get current HEAD commit SHA hash.

    This function must handle failure gracefully. The caller must not expect this
    function to be always successful.
    """
    enderror = (
        "Absolute links to paths will be omitted from the SBOM! You can specify the "
        "--ref flag to specify the commit SHA/tag manually."
    )

    git_exe = shutil.which("git")
    if git_exe is None:
        print("WARNING: Couldn't find git executable!", enderror, file=sys.stderr)
        return None
    args = [git_exe, "rev-parse", "--verify", "HEAD"]
    result = subprocess.run(args, stdout=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(
            "WARNING: The command '",
            " ".join(args),
            "' exitted with exit status ",
            result.returncode,
            "! Are you in a release archive not managed by git? ",
            enderror,
            sep="",
            file=sys.stderr,
        )
        return None
    return result.stdout.strip()


def _generate_timestamp() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _get_patches(wrap_file: Path) -> typing.Iterable[str]:
    """List all patches used.

    This should use the most authoritative source to determine currently used patches.
    The wrap file from the builddir is used.
    """
    config = configparser.ConfigParser()
    config.read(wrap_file)
    return [
        patch.strip() for patch in config["wrap-file"]["diff_files"].strip().split(",")
    ]


def _process_patch(
    patch: Path, base_path: Path, prefix: Path, get_url: url_func
) -> dict:
    """Generate CycloneDX info for a single patch.

    Arguments:
        patch: Path to the patch.
        base_path: Base path of the patch which should be removed from the patch path
          when creating a permalink.
        prefix: Path which should be prepended to patch path after base_path is removed
          from it.
        get_url: Function accepting a Path object and returning an URL pointing to that
          path.
    """
    with patch.open() as patch_file:
        result = {
            "type": "unofficial",
            "diff": {"text": {"content": patch_file.read()}},
        }
    if get_url is not None:
        result["diff"]["url"] = get_url(prefix / patch.relative_to(base_path))
    return result


def _merge_patches(
    primary_group: typing.Iterable[dict], secondary_group: typing.Iterable[dict]
) -> list[dict]:
    """Merge two patch groups with primary_group having precedence.

    This script autodetects and autofills info about patches it does not know
    beforehand. This is done to make sure that the SBOM is accurate even when patches
    are added and nobody remembers to update this script.

    Known patches (those in the primary group) include extra info which cannot be
    autodetected (purpose of the patch, external source). They should therefore have
    precedence.

    Arguments:
        primary_group: Patches which have priority (they will not be overwritten by
          second group).
        secondary_group: Patches which will be added to the returned list of patches
          if they do not collide with any patch from the primary group.
    """
    # Try to retrieve a patch from any of the groups. It does not matter which one is
    # picked. If both groups are empty, get None.
    first_patch = next(
        (patch for patch in primary_group),
        next((patch for patch in secondary_group), None),
    )
    if first_patch is None:
        raise ValueError("No patches for merging specified!")

    allowed_secondary_group = []

    if "url" in first_patch["diff"]:
        # If the first patch in any of the groups has the "url" key specified,
        # then all of the patches have to have the "url" key specified.
        # If that's the case, use the "url" key as the main key in the set as it
        # isn't that long, it doesn't contain newlines and it describes the
        # patch better.
        urls = {patch["diff"]["url"] for patch in primary_group}
        for secondary_patch in secondary_group:
            if secondary_patch["diff"]["url"] not in urls:
                allowed_secondary_group += secondary_patch
    else:
        sources = {patch["diff"]["text"]["content"] for patch in primary_group}
        for secondary_patch in secondary_group:
            if secondary_patch["diff"]["text"]["content"] not in sources:
                allowed_secondary_group += secondary_patch
    if isinstance(primary_group, list):
        return primary_group + allowed_secondary_group
    else:
        return list(
            itertools.chain(
                (patch for patch in primary_group),
                (patch for patch in allowed_secondary_group),
            )
        )


def _decode_atl_version(encoded_version_number: int) -> str:
    """Convert ATL version into more human-readable form.

    0xFF00 portion of ATL_VER is the major version number and 0x00FF is the minor
    version number.
    """
    return f"{encoded_version_number >> 8}.{encoded_version_number & 0xFF}"


def _get_windows_version() -> str:
    try:
        import winreg
    except ModuleNotFoundError:
        sys.exit(
            "This script must be run on Windows! If you want to test it on other "
            "platforms, use the --fake-windows-version flag."
        )
    # Use the version from platform module with the update revision added from the
    # registry.
    reg_key = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    )
    ubr, _ = winreg.QueryValueEx(reg_key, "UBR")
    winreg.CloseKey(reg_key)
    return f"{platform.version()}.{ubr}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("source_dir", help="Path of the source directory")
    parser.add_argument("purl", help="purl of this package")
    parser.add_argument(
        "project_version", help="Real version (possibly with p suffix) of AdbWinApi"
    )
    parser.add_argument(
        "underlying_version", help="Version of platform/development underlying project"
    )
    parser.add_argument(
        "repolink_format",
        help=(
            "A format string representing a permanent link to a file. Must contain "
            "the ${path} substitution. May contain the ${ref} substitution."
        ),
    )
    parser.add_argument(
        "--ref",
        help=(
            "Specify ${ref} for repolink_format argument. Unused if not used in "
            "repolink_format. If repolink_format requests ${ref} but it is not "
            "overriden, this script will try to retrieve the current git hash with "
            "git. If that is not successful, a warning is issued and sections "
            "requiring file links are ommited."
        ),
    )
    parser.add_argument(
        "base_repoling",
        help=(
            "A link to the repository. It is used to fill out the homepage, the vcs "
            "link (base_repoling + .git) and the issue tracker link (base_repoling + "
            "/issues)."
        ),
    )
    parser.add_argument(
        "--fake-windows-version",
        help=(
            "Fake the Windows version. Useful when testing this script on non-Windows "
            "hosts"
        ),
        action="store_true",
    )
    parser.add_argument(
        "--github-runner",
        help=(
            "Name of the GitHub runner used to build the library. If not specified, "
            "it is left out of the SBOM (it is assumed that this component was not "
            "used during the build)."
        ),
    )
    parser.add_argument(
        "--msvc-dev-cmd",
        help=(
            "Version of ilammy/msvc-dev-cmd GitHub Action. If not specified, it is "
            "left out of the SBOM (it is assumed that this component was not used "
            "during the build)."
        ),
    )
    parser.add_argument(
        "--action-gh-release",
        help=(
            "Version of softprops/action-gh-release GitHub Action. If not specified, "
            "it is left out of the SBOM (it is assumed that this component was not "
            "used during the build)."
        ),
    )
    parser.add_argument("target_architecture", help="Target architecture")
    parser.add_argument("target_endian", help="Target endian")
    parser.add_argument("meson_version", help="Version of Meson used")
    parser.add_argument("msvc_version", help="Version of MSVC")
    parser.add_argument("_MSC_VER", help="Value of _MSC_VER MSVC macro")
    parser.add_argument("_MSC_FULL_VER", help="Value of _MSC_FULL_VER MSVC macro")
    parser.add_argument(
        "_ATL_VER", help="Value of _ATL_VER ATL macro (may be specified in hex)"
    )
    args = parser.parse_args()

    repolink_template = string.Template(args.repolink_format)

    if "path" not in repolink_template.get_identifiers():
        sys.exit("The repolink_format argument must contain a ${path} substitution!")

    # Facilitate a flexible mechanism for making repo links to files.
    # This mechanism does not hardcode the repository name or owner.
    # It optionaly supports ref substitution, which will include the commit SHA/tag
    # in the link making it permanent.
    if "ref" in repolink_template.get_identifiers():
        if args.ref is not None:

            def get_file_link(path: str) -> str:  # noqa: D103
                return repolink_template.substitute(path=path, ref=args.ref)

        else:
            hash = _git_get_current_commit_hash()
            if hash is None:
                get_file_link = None
            else:

                # This is used as a more advanced and easy to read lambda, no need to
                # docstring it for D103.
                def get_file_link(path: str) -> str:  # noqa: D103
                    return repolink_template.substitute(path=path, ref=hash)

    if args.fake_windows_version:
        windows_version = "invalid_version_this_SBOM_is_invalid"
        lifecycle = "design"
    else:
        windows_version = _get_windows_version()
        lifecycle = "build"

    sourcedir = Path(args.source_dir)

    platform_tools_archive_sha256sum = _sha256_hash_file(
        sourcedir
        / f"subprojects/packagefiles/platform-tools-{args.underlying_version}.tar.gz"
    )

    atl_version = _decode_atl_version(int(args._ATL_VER, 0))

    purl_db = {
        "adbwinapi": f"{args.purl}@{args.project_version}",
        "windows": "pkg:microsoft/windows@" + windows_version,
        "msvc": "pkg:generic/msvc@" + args.msvc_version,
        "atl": "pkg:generic/atl@" + atl_version,
        "meson": "pkg:pypi/meson@" + args.meson_version,
    }

    if args.msvc_dev_cmd is not None:
        purl_db["ilammy/msvc-dev-cmd"] = (
            "pkg:github/ilammy/msvc-dev-cmd@" + args.msvc_dev_cmd
        )

    if args.action_gh_release is not None:
        purl_db["softprops/action-gh-release"] = (
            "pkg:github/softprops/action-gh-release@" + args.action_gh_release
        )

    if args.github_runner is not None:
        purl_db["github_runner"] = (
            "pkg:generic/github-actions-runner@" + args.github_runner
        )

    #
    # Real SBOM definitions start here
    #

    apache_license = {
        "id": "Apache-2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    }

    apache_license_extref = {
        "type": "license",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    }

    mit_license = {
        "id": "MIT",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    }

    platform_tools_archive_hash = {
        "alg": "SHA-256",
        "content": platform_tools_archive_sha256sum,
    }

    target_arch_prop = [
        {
            "name": "target.architecture",
            "value": args.target_architecture,
        },
        {
            "name": "target.endian",
            "value": args.target_endian,
        },
        {
            "name": "target.os",
            "value": "windows",
        },
    ]

    platform_development = {
        "type": "library",
        "supplier": {
            "name": "Google",
        },
        "name": "platform/development",
        "description": (
            "Official and original source code for AdbWinApi and AdbWinUsbApi"
        ),
        "version": args.underlying_version,
        "hashes": [platform_tools_archive_hash],
        "externalReferences": [
            {
                "type": "vcs",
                "url": "https://android.googlesource.com/platform/development",
            },
            {
                "type": "distribution",
                "url": (
                    source_archive_url.source_archive_url
                    % {"version": args.underlying_version}
                ),
                "comment": (
                    "GitHub's git server does not provide stable release archives. "
                    "Every time you try to download it, it will have a different "
                    "hash. This means that you will most likely not be able to "
                    "validate the hash specified here. It is provided for "
                    "completeness only."
                ),
                "hashes": [platform_tools_archive_hash],
            },
        ],
    }

    cast_errors_patch = _process_patch(
        sourcedir
        / "subprojects/packagefiles/diff_files/0001-fix-bool-to-ptr-implicit-cast-errors.patch",
        sourcedir,
        Path("build_template"),
        get_file_link,
    )
    cast_errors_patch["resolves"] = [
        {
            "type": "defect",
            "name": "FTBFS",
            "description": (
                "Newer versions of MSVC aren't as lenient to implicitly cast types as "
                "they used to be; this patch makes the project buildable on newer "
                "MSVC versions."
            ),
        }
    ]

    fix_build_patch = _process_patch(
        sourcedir / "subprojects/packagefiles/diff_files/0002-fix-build.patch",
        sourcedir,
        Path("build_template"),
        get_file_link,
    )
    fix_build_patch["resolves"] = [
        {
            "type": "defect",
            "name": "FTBFS",
            "description": "Patch taken from MSYS2 project which fixes build.",
            "references": [
                "https://github.com/msys2/adbwinapi/blob/7a4dd0c3e0369493d6f6b3e3aa9f1e9f5bd3fb0f/0001-adbwinusb-fix-build.patch"
            ],
        }
    ]

    known_patches = [
        cast_errors_patch,
        fix_build_patch,
    ]

    all_patches = _merge_patches(
        known_patches,
        (
            _process_patch(
                sourcedir / "subprojects/packagefiles" / patch_relpath,
                sourcedir,
                Path("build_template"),
                get_file_link,
            )
            for patch_relpath in _get_patches(
                sourcedir / "subprojects/development.wrap"
            )
        ),
    )

    msys2_adbwinapi = {
        "type": "library",
        "authors": [{"name": "Biswapriyo Nath", "email": "nathbappai@gmail.com"}],
        "name": "adbwinapi",
        "description": (
            "A CMake port of platform/development for use in MSYS2's android-tools"
        ),
        "licenses": [{"license": apache_license}],
        "pedigree": {
            "ancestors": [platform_development],
        },
        "externalReferences": [
            {
                "type": "website",
                "url": args.base_repoling,
            },
            {
                "type": "vcs",
                "url": args.base_repoling + ".git",
            },
            {
                "type": "issue-tracker",
                "url": args.base_repoling + "/issues",
            },
            apache_license_extref,
        ],
    }

    github_actions = []

    if args.msvc_dev_cmd is not None:
        github_actions.append(
            {
                # Close enough.
                "type": "library",
                "name": "ilammy/msvc-dev-cmd",
                "description": "GitHub Action used to setup MSVC environment",
                "supplier": {
                    "name": "GitHub, Inc.",
                    "url": ["https://github.com/"],
                },
                "version": args.msvc_dev_cmd,
                "bom-ref": purl_db["ilammy/msvc-dev-cmd"],
                "purl": purl_db["ilammy/msvc-dev-cmd"],
                "externalReferences": [
                    {
                        "type": "website",
                        "url": "https://github.com/ilammy/msvc-dev-cmd",
                    },
                    {
                        "type": "license",
                        "url": (
                            "https://github.com/ilammy/msvc-dev-cmd/blob/master/LICENSE"
                        ),
                    },
                ],
                "licenses": [{"license": mit_license}],
            }
        )

    if args.action_gh_release is not None:
        github_actions.append(
            {
                "type": "library",
                "name": "softprops/action-gh-release",
                "description": "GitHub Action used to publish GitHub Releases",
                "supplier": {
                    "name": "GitHub, Inc.",
                    "url": ["https://github.com/"],
                },
                "version": args.action_gh_release,
                "bom-ref": purl_db["softprops/action-gh-release"],
                "purl": purl_db["softprops/action-gh-release"],
                "externalReferences": [
                    {
                        "type": "website",
                        "url": "https://github.com/softprops/action-gh-release",
                    },
                    {
                        "type": "license",
                        "url": (
                            "https://github.com/softprops/action-gh-release/blob/master/LICENSE"
                        ),
                    },
                ],
                "licenses": [{"license": mit_license}],
            }
        )

    if args.github_runner is not None:
        # It is unnecessary to remove all common prefixes from all supported GitHub
        # runners since only Windows runners are able to build AdbWinApi. But let's do
        # it anyway.
        for runner in ("windows", "macos", "ubuntu"):
            if args.github_runner.startswith(runner + "-"):
                github_runner_name = runner
                github_runner_version = args.github_runner.removeprefix(runner + "-")
                break
        else:
            sys.exit(
                f"The GitHub runner '{args.github_runner}' has an unrecognized "
                "prefix. If it is a custom runner, you should know that this script "
                "currently supports official GitHub runners only (but adding support "
                "for it shouldn't be difficult)."
            )
        github_actions.append(
            {
                "type": "platform",
                "name": github_runner_name,
                "description": (
                    "Official GitHub runner used to build the library. Tools provided "
                    "by it by default may be used during the build."
                ),
                "supplier": {
                    "name": "GitHub, Inc.",
                    "url": ["https://github.com/"],
                },
                "version": github_runner_version,
                "bom-ref": purl_db["github_runner"],
                "purl": purl_db["github_runner"],
                "externalReferences": [
                    {
                        "type": "website",
                        "url": "https://github.com/actions/runner-images",
                    },
                ],
                "properties": [
                    {
                        "name": "github_runner_name",
                        "value": args.github_runner,
                    }
                ],
            }
        )

    document = {
        "$schema": "https://cyclonedx.org/schema/bom-1.6.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": uuid.uuid4().urn,
        "version": 1,
        "metadata": {
            "timestamp": _generate_timestamp(),
            "lifecycles": [{"phase": lifecycle}],
            "supplier": {
                "name": "GitHub, Inc.",
                "url": ["https://github.com/"],
            },
            "component": {
                "type": "library",
                "authors": [
                    {
                        "name": "meator",
                        "email": "meator.dev@gmail.com",
                    }
                ],
                "name": "AdbWinApi",
                "version": args.project_version,
                "bom-ref": purl_db["adbwinapi"],
                "purl": purl_db["adbwinapi"],
                "description": "Windows support libraries for android-tools",
                "pedigree": {
                    "ancestors": [msys2_adbwinapi],
                    "patches": all_patches,
                },
                "externalReferences": [
                    {"type": "website", "url": "https://github.com/meator/AdbWinApi"},
                    {"type": "vcs", "url": "https://github.com/meator/AdbWinApi.git"},
                    {
                        "type": "issue-tracker",
                        "url": "https://github.com/meator/AdbWinApi/issues",
                    },
                    apache_license_extref,
                ],
                "licenses": [{"license": apache_license}],
                "properties": target_arch_prop,
            },
        },
        "components": (
            [
                {
                    "type": "operating-system",
                    "name": "Microsoft Windows",
                    "version": windows_version,
                    "bom-ref": purl_db["windows"],
                    "purl": purl_db["windows"],
                },
                {
                    "type": "application",
                    "name": "MSVC",
                    "version": args.msvc_version,
                    "supplier": {
                        "name": "Microsoft",
                    },
                    "bom-ref": purl_db["msvc"],
                    "purl": purl_db["msvc"],
                    "properties": (
                        [
                            {
                                "name": "_MSC_VER",
                                "value": args._MSC_VER,
                            },
                            {
                                "name": "_MSC_FULL_VER",
                                "value": args._MSC_FULL_VER,
                            },
                        ]
                        + target_arch_prop
                    ),
                },
                {
                    "type": "library",
                    "name": "ATL",
                    "description": "Active Template Library",
                    "version": atl_version,
                    "supplier": {
                        "name": "Microsoft",
                    },
                    "bom-ref": purl_db["atl"],
                    "purl": purl_db["atl"],
                    "properties": (
                        [{"name": "_ATL_VER", "value": str(int(args._ATL_VER, 0))}]
                        + target_arch_prop
                    ),
                },
                {
                    "type": "application",
                    "name": "meson",
                    "description": "Meson build system",
                    "version": args.meson_version,
                    "supplier": {
                        "name": "Python Package Index",
                        "url": ["https://pypi.org/"],
                    },
                    "bom-ref": purl_db["meson"],
                    "purl": purl_db["meson"],
                    "licenses": [{"license": apache_license}],
                    "externalReferences": [apache_license_extref],
                },
            ]
            + github_actions
        ),
        "dependencies": [
            {
                "ref": purl_db["adbwinapi"],
                "dependsOn": [
                    purl_db["windows"],
                    purl_db["msvc"],
                    purl_db["atl"],
                    purl_db["meson"],
                ],
            }
        ],
    }

    if args.msvc_dev_cmd is not None:
        document["dependencies"][0]["dependsOn"].append(purl_db["ilammy/msvc-dev-cmd"])

    if args.action_gh_release is not None:
        document["dependencies"][0]["dependsOn"].append(
            purl_db["softprops/action-gh-release"]
        )

    if args.github_runner is not None:
        document["dependencies"][0]["dependsOn"].append(purl_db["github_runner"])

    try:
        json.dump(document, sys.stdout)
    except OSError as exc:
        sys.exit(str(exc))
