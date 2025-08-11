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

# Be careful when using dollar signs ($$) in the original source for this file
# (in build_template). This file is passed through Python's string.Template by
# initialize_build_template.py. Even comments are affected.

project(
  'AdbWinApi-toplevel',
  'cpp',
  version: '${project_version}',
  default_options: ['warning_level=3'],
)

subproject('development')

if get_option('generate_sbom')
  CXX = meson.get_compiler('cpp')
  _MSC_VER = CXX.get_define('_MSC_VER')
  _MSC_FULL_VER = CXX.get_define('_MSC_FULL_VER')
  _ATL_VER = CXX.get_define('_ATL_VER', prefix: '#include <atldef.h>')

  if get_option('sbom_name') != ''
    sbom_name = get_option('sbom_name')
  else
    sbom_name = 'AdbWinApi-@0@-sbom.cyclonedx.json'.format(meson.project_version())
  endif

  extra_args = []

  if get_option('github_runner_ver') != ''
    extra_args += ['--github-runner', get_option('github_runner_ver')]
  endif
  if get_option('sbom_msvc_dev_cmd_ver') != ''
    extra_args += ['--msvc-dev-cmd', get_option('sbom_msvc_dev_cmd_ver')]
  endif
  if get_option('sbom_action_gh_release') != ''
    extra_args += ['--action-gh-release', get_option('sbom_action_gh_release')]
  endif

  custom_target(
    command: [
      'generate_sbom.py',
      meson.project_source_root(),
      'pkg:github/meator/AdbWinApi',
      meson.project_version(),
      '${version}',
      # Beware! The source file (in build_template) contains two
      # dollar signs. initialize_build_template.py substitutes
      # these into a single dollar sign.
      'https://github.com/meator/AdbWinApi/blob/$${ref}/$${path}',
      'https://github.com/meator/AdbWinApi',
      host_machine.cpu_family(),
      host_machine.endian(),
      meson.version(),
      CXX.version(),
      _MSC_VER,
      _MSC_FULL_VER,
      _ATL_VER,
      extra_args,
    ],
    capture: true,
    output: sbom_name,
    install: true,
    install_dir: get_option('sbom_dir'),
  )
endif
