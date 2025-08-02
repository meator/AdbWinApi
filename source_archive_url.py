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

"""Helper module containing variables related to platform/development."""

# These variables are used in initialize_build_template.py and generate_sbom.py

# #######################################################
# #               WARNING WARNING WARNING               #
# #               =======================               #
# # If you edit this file, make sure that you rerun     #
# # initialize_build_template.py, otherise your changes #
# # will not take effect in generate_sbom.py!           #
# #######################################################
#
# You can disregard the message above if you are using a -src
# release archive, as it does not include initialize_build_template.py.

source_archive_url = "https://android.googlesource.com/platform/development.git/+archive/platform-tools-%(version)s.tar.gz"
# This should be updated when a new version of platform-tools is used.
# But it is only an approximation and new updates shouldn't change the
# size of the archive that much.
source_archive_approximate_size = 262_259_245
