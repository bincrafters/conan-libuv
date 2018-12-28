#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from conans import ConanFile, tools
from conans.errors import ConanInvalidConfiguration


class LibuvConan(ConanFile):
    name = "libuv"
    version = "1.24.0"
    description = "Cross-platform asynchronous I/O "
    url = "https://github.com/bincrafters/conan-libuv"
    homepage = "https://github.com/libuv/libuv"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "MIT"
    exports = ["LICENSE.md"]
    settings = "os", "arch", "compiler", "build_type"
    generators = "cmake"
    options = {"shared": [True, False]}
    default_options = {"shared": False}
    _root_folder = name + "-" + version

    def configure(self):
        del self.settings.compiler.libcxx
        if self.settings.compiler == "Visual Studio" \
            and int(str(self.settings.compiler.version)) < 14:
            raise ConanInvalidConfiguration("Visual Studio >= 14 (2015) is required")

    def source(self):
        tools.get("{0}/archive/v{1}.tar.gz".format(self.homepage, self.version))

    def build_requirements(self):
        self.build_requires("gyp_installer/20181217@bincrafters/stable")
        if not tools.which("ninja"):
            self.build_requires("ninja_installer/1.8.2@bincrafters/stable")

    def build(self):
        with tools.chdir(self._root_folder):
            env_vars = dict()
            if self.settings.compiler == "Visual Studio":
                env_vars["GYP_MSVS_VERSION"] = {"14": "2015",
                                                "15": "2017"}.get(str(self.settings.compiler.version))
            with tools.environment_append(env_vars):
                target_arch = {"x86": "ia32", "x86_64": "x64"}.get(str(self.settings.arch))
                uv_library = "shared_library" if self.options.shared else "static_library"
                self.run("python gyp_uv.py -f ninja -Dtarget_arch=%s -Duv_library=%s"
                         % (target_arch, uv_library))
                self.run("ninja -C out/%s" % self.settings.build_type)

    def package(self):
        self.copy(pattern="*.h", dst="include", src=os.path.join(self._root_folder, "include"))
        bin_dir = os.path.join(self._root_folder, "out", str(self.settings.build_type))
        if self.settings.os == "Windows":
            if self.options.shared:
                self.copy(pattern="*.dll", dst="bin", src=bin_dir, keep_path=False)
            self.copy(pattern="*.lib", dst="lib", src=bin_dir, keep_path=False)
        elif str(self.settings.os) in ["Linux", "Android"]:
            if self.options.shared:
                self.copy(pattern="libuv.so.1", dst="lib", src=os.path.join(bin_dir, "lib"),
                          keep_path=False)
                lib_dir = os.path.join(self.package_folder, "lib")
                os.symlink("libuv.so.1", os.path.join(lib_dir, "libuv.so"))
            else:
                self.copy(pattern="*.a", dst="lib", src=bin_dir, keep_path=False)
        elif str(self.settings.os) in ["Macos", "iOS", "watchOS", "tvOS"]:
            if self.options.shared:
                self.copy(pattern="*.dylib", dst="lib", src=bin_dir, keep_path=False)
            else:
                self.copy(pattern="*.a", dst="lib", src=bin_dir, keep_path=False)

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.libs = ["libuv.dll.lib" if self.options.shared else "libuv"]
            self.cpp_info.libs.extend(["Psapi", "Ws2_32", "Iphlpapi", "Userenv"])
        else:
            self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.libs.append("pthread")
