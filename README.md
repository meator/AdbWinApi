# AdbWinApi
> [!IMPORTANT]
> This projet is still work in progress. No git history linearity guarantees are
> made (I reserve the right to force push to `main` until I finish the project).

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

Dynamic libraries are provided for x86-64 (64bit), x86 (32bit) and ARM64 (aarch64).

The main inspiration for this project is https://github.com/msys2/adbwinapi.
This repository is a Meson rewrite of its CMake build system. It also provides
the following additional features:

- direct support for x86 and ARM64
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

First, launch your Developer Command Prompt. Then proceed with the build:

```powershell
# Clone this repository if you don't have it already.
git clone https://github.com/meator/AdbWinApi.git
cd AdbWinApi
# Set up the source tree (you can choose the output folder).
# The following command will download msys2/adbwinapi, which
# can take a minute.
python initialize_build_template.py srcdir
# Enter the newly created source tree.
cd srcdir
# Setup the builddir.
meson setup build
# NOTE: If you want to use the same build flags that are used
#       for prebuilt libraries, run the following command instead.
#meson setup build --native-file ..\release_install_native.ini
# The native file will switch the VC++ runtime to MT (static version)
# it will alter instalation directories (do not attempt to install
# it to your system! these settings are meant for deployment)
# and it will activate release mode.

# Compile the project.
meson compile -C build
# Optionally install the project (if you haven't used
# release_install_native.ini as described above).
meson install -C build
```

## Versioning
This project follows [nmeum/android-tools](https://github.com/nmeum/android-tools)'
versioning scheme, which is **major.minor.patch[brevision number]**.
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
- `35.0.2` - both this project and the underlying
  [platform/development](https://android.googlesource.com/platform/development.git)
  repository have version `35.0.2`
- `35.0.2p1` - this project has two `35.0.2` releases differentiated by the
  `p<num>` suffix, `35.0.2p1` is the newer one, the version of android-tools
  is `35.0.2`, which is same as the project version with the `p<num>` suffix
  stripped

## Deployment process
Here is a diagram describing the build process during release deployment:

![diagram](etc/Build and deployment process.svg)

## Release procedure
> [!NOTE]
> If you do not have commit access to this repository (i.e. you are not
> [meator](https://github.com/meator)), these instructions likely won't mean
> a lot to you. But they may still be interesting if you want to test
> reproducibility and know the origin of the prebuilt files.

1. Update `VERSION.txt` and `ANDROID_TOOLS_VERSION.txt`
2. Commit it signed with key `0x7B0F58A5E0F1A2EA11578A731A14CB3464CBE5BF`.

   The commit title is `Released version <new VERSION.txt contents>`

   The commit description includes a list of changes which will be included
   at the top of the GitHub Releases page.
3. Create a signed annotated tag with key `0x7B0F58A5E0F1A2EA11578A731A14CB3464CBE5BF`

   ```
   git tag <VERSION.txt contents> -a -s
   ```

   The tag title is `<new VERSION.txt contents>`

   The tag description is identical to the commit description.
4. Push the tag to `meator/AdbWinApi`
5. Download `SHA256SUM.txt` release artifact
6. Create a detached signature with key `0x7B0F58A5E0F1A2EA11578A731A14CB3464CBE5BF`

   ```
   gpg2 --local-user 7B0F58A5E0F1A2EA11578A731A14CB3464CBE5BF --output SHA256SUM.sig --detach-sig SHA256SUM.txt 
   ```
7. Edit the release and upload `SHA256SUM.sig` as a release artifact

## License
Like [msys2/adbwinapi](https://github.com/msys2/adbwinapi), this repository
is licensed with the same [Apache-2.0 license](LICENSE) used in AOSP
[platform/development](https://android.googlesource.com/platform/development.git)
repository.
