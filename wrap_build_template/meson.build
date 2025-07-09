project('AdbWinApi', 'cpp', version: '${project_version}')

# Do some sanity checking so that meson can fail early instead of at final link time
if host_machine.system() != 'windows'
  error(
    'This AdbWinApi prebuilt wrap (like the source version) targets',
    f'Windows. Expected \'windows\', got \'@host_machine.system()@\'',
  )
endif

if host_machine.cpu_family() not in ['x86_64', 'x86', 'aarch64']
  error(
    'This AdbWinApi prebuilt wrap currently only bundles x86_64',
    '(64bit), x86 (32bit) and aarch64 (ARM64) versions of AdbWinApi.',
    'You will have to built AdbWinApi yourself. Expected \'x86_64\',',
    f'\'x86\' or \'aarch64\', got \'@host_machine.cpu_family()@\'',
  )
endif

dist_dir = meson.current_source_dir() / host_machine.cpu_family()

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
