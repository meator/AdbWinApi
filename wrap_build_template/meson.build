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

project('AdbWinApi', 'cpp', version: '${project_version}', license: 'Apache-2.0')

# Do some sanity checking so that meson can fail early instead of at final link time
if host_machine.system() != 'windows'
  error(
    'This AdbWinApi prebuilt wrap (like the source version) targets',
    'Windows. Expected \'windows\', got \'@0@\''.format(host_machine.system()),
  )
endif

if host_machine.cpu_family() not in ['x86_64', 'x86', 'aarch64']
  error(
    'This AdbWinApi prebuilt wrap currently only bundles x86_64',
    '(64bit), x86 (32bit) and aarch64 (ARM64) versions of AdbWinApi.',
    'You will have to built AdbWinApi yourself. Expected \'x86_64\',',
    '\'x86\' or \'aarch64\', got \'@0@\''.format(host_machine.cpu_family()),
  )
endif

dist_dir = meson.current_source_dir() / host_machine.cpu_family()

if get_option('adbwinapi_install')
  install_data(
    dist_dir / 'AdbWinApi.dll',
    dist_dir / 'AdbWinUsbApi.dll',
    install_dir: get_option('libdir'),
  )
endif

cxx = meson.get_compiler('cpp')
adbwinapi_dep = declare_dependency(
  dependencies: cxx.find_library('AdbWinApi', dirs: dist_dir),
  include_directories: 'include/host/windows/usb/api',
  version: '${library_version}',
)
adbwinusbapi_dep = declare_dependency(
  dependencies: cxx.find_library('AdbWinUsbApi', dirs: dist_dir),
  version: '${library_version}',
)

meson.override_dependency('AdbWinApi', adbwinapi_dep)
meson.override_dependency('AdbWinUsbApi', adbwinusbapi_dep)
