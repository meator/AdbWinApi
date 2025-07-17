# AdbWinApi
This repository provides a prebuilt version of AdbWinApi from
https://android.googlesource.com/platform/development. It is provided in
[Meson Wrap](https://mesonbuild.com/Wrap-dependency-system-manual.html) form,
which makes integration into Meson projects simple.

AdbWinApi and AdbWinUsbApi are dependencies of android-tools (which includes
`adb`, `fastboot` and other Android tools). It is impractical to build these
as part of android-tools, because AdbWinApi and AdbWinUsbApi require MSVC with
access to some VC++ components (for example
[ATL](https://learn.microsoft.com/en-us/cpp/mfc/mfc-and-atl)), whereas the
rest of android-tools expects a Cygwin compiler.

Dynamic libraries are provided for **x86-64 (64bit), x86 (32bit) and ARM64
(aarch64)**.

The main inspiration for this project is https://github.com/msys2/adbwinapi.
This repository is a Meson rewrite of its CMake build system. It also provides
the following additional features:

- transparent build process (release artifacts are built using a [GitHub
  Action](./.github/workflows/release.yml))
- all the nicities of Meson (cross/native files, `compile_commands.json` by default)
  etc.
- this project is distributed as a Meson Wrap, so everything is handled by this
  project, users can simply call `dependency('AdbWinApi')`
- better documented release procedure
- better documented build procedure

## Building manually
### Dependencies
- [Meson](https://mesonbuild.com/)
- [Ninja](https://ninja-build.org/) (usually distributed with Meson) or MSBuild
- MSVC
- [ATL](https://learn.microsoft.com/en-us/cpp/mfc/mfc-and-atl) (usually
  distributed with MSVC)
- Python 3

> [!WARNING]
> Do not use Cygwin, MSYS2, WSL1/WSL2 or similar environments. This project
> requires MSVC.

The process differs depending on whether you use the `AdbWinApi-<ver>-src.zip`
source archive, or use GitHub's default source archives or clone the repository.
Using the `AdbWinApi-<ver>-src.zip` source archive is simpler.

#### Building from source archive
First, launch your Developer Command Prompt. Then proceed with the build:
```powershell
# Extract the source and enter it.
Expand-Archive AdbWinApi-$VER-src.zip
cd AdbWinApi-$VER-src
# Setup the builddir.
meson setup build
# If you want to build libraries similar to the prebuilt release ones,
# you can add the following flags:
#meson setup build --buildtype release -Db_vscrt=mt
# This will switch the VC++ runtime to MC (static version) and it will
# build the libraries with release optimizations.

# Compile the project.
meson compile -C build
# Optionally install the project.
meson install -C build
```

#### Building from GitHub's source archive or git
First, launch your Developer Command Prompt. Then proceed with the build:
```powershell
# Clone this repository if you don't have it already.
git clone https://github.com/meator/AdbWinApi.git
cd AdbWinApi
# OR extract GitHub's archive and enter it:
Expand-Archive AdbWinApi-$VER.zip
cd AdbWinApi-$VER

# Set up the source tree (you can choose the output folder).
# The following command will download msys2/adbwinapi, which
# can take a minute.
python initialize_build_template.py srcdir
# Enter the newly created source tree.
cd srcdir
# Setup the builddir.
meson setup build
# If you want to build libraries similar to the prebuilt release ones,
# you can add the following flags:
#meson setup build --buildtype release -Db_vscrt=mt
# This will switch the VC++ runtime to MC (static version) and it will
# build the libraries with release optimizations.

# Compile the project.
meson compile -C build
# Optionally install the project.
meson install -C build
```

## Versioning
This project follows [nmeum/android-tools](https://github.com/nmeum/android-tools)'
versioning scheme, which is **major.minor.patch[prevision number]**.
The _major_, _minor_ and _patch_ number correspond to the version of
android-tools the version is targeting. A `p<revision number>` is added
to the version if it is needed to update this project before the next
release of android-tools.

The exact version of android-tools can be found in the last line of
`ANDROID_TOOLS_VERSION.txt`. This version can be obtained by running
`dependency('AdbWinApi').version()`. If the current version of this project
doesn't have a `p` revision suffix, the versions in `ANDROID_TOOLS_VERSION.txt`
and `VERSION.txt` shall be identical.

Examples:
- `35.0.2` - both this project _and_ the underlying
  [platform/development](https://android.googlesource.com/platform/development.git)
  repository have version `35.0.2`
- `35.0.2p1` - this project has two `35.0.2` releases differentiated by the
  `p<num>` suffix, `35.0.2p1` is the newer one, the version of android-tools
  is `35.0.2`, which is same as the project version with the `p<num>` suffix
  stripped

## Deployment process
Here is a diagram describing the build process during release deployment:

![diagram](./etc/Build%20and%20deployment%20process.svg)

## Release procedure
> [!NOTE]
> If you do not have commit access to this repository (i.e. you are not
> [meator](https://github.com/meator)), these instructions likely won't mean
> a lot to you.

1. Update `VERSION.txt` and `ANDROID_TOOLS_VERSION.txt`
2. Commit it signed with key `0x7B0F58A5E0F1A2EA11578A731A14CB3464CBE5BF`.

   The commit title is `Released version <new VERSION.txt contents>`

   The commit description includes a list of changes which will be included
   at the top of the GitHub Releases page.
3. Create a signed annotated tag with key `0x7B0F58A5E0F1A2EA11578A731A14CB3464CBE5BF`

   ```
   git tag <VERSION.txt contents> -a -s -u 7B0F58A5E0F1A2EA11578A731A14CB3464CBE5BF
   ```

   The tag title is `<new VERSION.txt contents>`

   The tag description is identical to the commit description.
4. Push the tag to `meator/AdbWinApi`
5. Download `SHA256SUM.txt` release artifact
6. Create a detached signature with key `0x7B0F58A5E0F1A2EA11578A731A14CB3464CBE5BF`

   ```
   gpg2 --armor --local-user 7B0F58A5E0F1A2EA11578A731A14CB3464CBE5BF --output SHA256SUM.txt.asc --detach-sig SHA256SUM.txt
   ```
7. Edit the release and upload `SHA256SUM.txt.asc` as a release artifact

## Notes
Prebuilt release artifacts currently **do not** follow the advice in
[`host/windows/usb/api/BUILDME.TXT`](https://android.googlesource.com/platform/development.git).
I do not know whether the instructions are still relevant, they were last
updated on [August 12,
2015](https://android.googlesource.com/platform/development.git/+/487b1deae9082ff68833adf9eb47d57557f8bf16).

I suspect that adapting the currently present GitHub action to use
the older Windows Driver Kit Version would be either difficult or
impossible. This would mean that I would have to compile and package
release artifacts manually, which is less transparent and more error-prone.

## License
Like [msys2/adbwinapi](https://github.com/msys2/adbwinapi), this repository
is licensed with the same [Apache-2.0 license](LICENSE) used in AOSP
[platform/development](https://android.googlesource.com/platform/development.git)
repository.
