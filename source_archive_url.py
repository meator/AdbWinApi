# These variables are used in initialize_build_template.py and generate_sbom.py

source_archive_url = "https://android.googlesource.com/platform/development.git/+archive/platform-tools-%(version)s.tar.gz"
# This should be updated when a new version of platform-tools is used.
# But it is only an approximation and new updates shouldn't change the
# size of the archive that much.
source_archive_approximate_size = 262_259_245
