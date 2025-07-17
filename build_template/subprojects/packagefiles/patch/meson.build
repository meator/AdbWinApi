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

project(
  'AdbWinApi',
  'cpp',
  default_options: [
    'warning_level=3',
    # Use MSVC's default std.
    # 'cpp_std=vc++14',
  ],
  version: '${project_version}',
  license: 'Apache-2.0',
)

if host_machine.system() != 'windows'
  error(
    'As its name implies, AdbWinApi can be only built for Windows targets!',
    'It relies on MSVC and on Windows internal libraries.',
  )
endif

if meson.get_compiler('cpp').get_id() != 'msvc'
  error(
    'ADB API for Windows can only be built using MSVC. This project',
    'depends on ATL, which is difficult to compile without MSVC:',
    'https://stackoverflow.com/q/57875554',
  )
endif

CXX = meson.get_compiler('cpp')

if not CXX.has_header('atlbase.h')
  error(
    'You are missing the ATL optional component of Visual C++.',
    'See https://learn.microsoft.com/en-us/cpp/mfc/mfc-and-atl',
  )
endif

# NOTE: setupapi and winusb could perhaps also benefit from checks like
# the one above.

windll_define = []

if meson.backend() == 'ninja'
  windll_define += '-D_WINDLL'
else
  # vs* backends add _WINDLL by default. msbuild itself seems to inject
  # it into the compiler commandline.
endif

# NOTE:
# Building these libraries statically would be difficult. They are meant
# to be compiled into .dlls. Even google's official android-tools zip
# bundles AdbWinApi.dll alongside adb.exe, fastboot.exe...

windows = import('windows')

adbwinapi_rc = windows.compile_resources(
  'host/windows/usb/api/AdbWinApi.rc',
)

adbwinapi_lib = shared_library(
  'AdbWinApi',
  'host/windows/usb/api/AdbWinApi.cpp',
  # This def file doesn't really do anything, it doesn't define
  # any EXPORTS. Ignore it.
  # 'host/windows/usb/api/AdbWinApi.def',
  adbwinapi_rc,
  'host/windows/usb/api/adb_api.cpp',
  'host/windows/usb/api/adb_api_instance.cpp',
  'host/windows/usb/api/adb_endpoint_object.cpp',
  'host/windows/usb/api/adb_helper_routines.cpp',
  'host/windows/usb/api/adb_interface.cpp',
  'host/windows/usb/api/adb_interface_enum.cpp',
  'host/windows/usb/api/adb_io_completion.cpp',
  'host/windows/usb/api/adb_legacy_endpoint_object.cpp',
  'host/windows/usb/api/adb_legacy_interface.cpp',
  'host/windows/usb/api/adb_legacy_io_completion.cpp',
  'host/windows/usb/api/adb_object_handle.cpp',
  'host/windows/usb/api/stdafx.cpp',
  cpp_args: [
    '-DADBWIN_EXPORTS',
    '-D_CRT_NON_CONFORMING_SWPRINTFS',
    '-D_CRT_SECURE_NO_WARNINGS',
    '-D_UNICODE',
    '-DUNICODE',
    '-DNTDDI_VERSION=NTDDI_WIN10',
    '-D_WIN32_WINNT=_WIN32_WINNT_WIN10',
    '-DWINVER=_WIN32_WINNT_WIN10',
    windll_define,
  ],
  version: '${version}',
  dependencies: CXX.find_library('setupapi'),
  install: true,
)

adbwinusbapi_rc = windows.compile_resources(
  'host/windows/usb/winusb/AdbWinUsbApi.rc',
)

shared_library(
  'AdbWinUsbApi',
  'host/windows/usb/winusb/AdbWinUsbApi.cpp',
  # See comment above.
  # 'development/host/windows/usb/winusb/AdbWinUsbApi.def',
  adbwinusbapi_rc,
  'host/windows/usb/winusb/adb_winusb_endpoint_object.cpp',
  'host/windows/usb/winusb/adb_winusb_interface.cpp',
  'host/windows/usb/winusb/adb_winusb_io_completion.cpp',
  'host/windows/usb/winusb/stdafx.cpp',
  cpp_args: [
    '-DADBWIN_EXPORTS',
    '-D_CRT_NON_CONFORMING_SWPRINTFS',
    '-D_CRT_SECURE_NO_WARNINGS',
    '-D_UNICODE',
    '-DUNICODE',
    '-DNTDDI_VERSION=NTDDI_WIN10',
    '-D_WIN32_WINNT=_WIN32_WINNT_WIN10',
    '-DWINVER=_WIN32_WINNT_WIN10',
    windll_define,
  ],
  link_with: adbwinapi_lib,
  version: '${version}',
  dependencies: CXX.find_library('winusb'),
  install: true,
)

if get_option('adbwinapi_install_headers')
  headers = files(
    'host/windows/usb/api/adb_api.h',
    'host/windows/usb/api/adb_api_instance.h',
    'host/windows/usb/api/adb_api_legacy.h',
    'host/windows/usb/api/adb_api_private_defines.h',
    'host/windows/usb/api/adb_endpoint_object.h',
    'host/windows/usb/api/adb_helper_routines.h',
    'host/windows/usb/api/adb_interface.h',
    'host/windows/usb/api/adb_interface_enum.h',
    'host/windows/usb/api/adb_io_completion.h',
    'host/windows/usb/api/adb_legacy_endpoint_object.h',
    'host/windows/usb/api/adb_legacy_interface.h',
    'host/windows/usb/api/adb_legacy_io_completion.h',
    'host/windows/usb/api/adb_object_handle.h',
    'host/windows/usb/api/adb_winusb_api.h',
    'host/windows/usb/api/Resource.h',
    'host/windows/usb/api/stdafx.h',
  )
  if get_option('adbwinapi_install_headers_subdir') == ''
    install_headers(headers)
  else
    install_headers(
      headers,
      subdir: get_option('adbwinapi_install_headers_subdir'),
    )
  endif
endif
