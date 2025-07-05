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
