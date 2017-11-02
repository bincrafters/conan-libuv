#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile
from conans import ConanFile, AutoToolsBuildEnvironment, tools


class LibuvConan(ConanFile):
    name = "libuv"
    version = "1.15.0"
    settings = "os", "arch", "compiler", "build_type"
    generators = "cmake"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    url = "https://github.com/bincrafters/conan-libuv"
    description = "Cross-platform asynchronous I/O "
    license = "https://github.com/libuv/libuv/blob/master/LICENSE"
    exports = "LICENSE"
    root = name + "-" + version
    install_dir = tempfile.mkdtemp(prefix=root)

    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        source_url = "https://github.com/libuv/libuv"
        tools.get("{0}/archive/v{1}.tar.gz".format(source_url, self.version))

    def build_requirements(self):
        self.build_requires("ninja_installer/1.8.2@bincrafters/testing")
        self.build_requires("gyp_installer/20171101@bincrafters/testing")

    def build(self):
        with tools.chdir(self.root):
            env_vars = dict()
            if self.settings.compiler == "Visual Studio":
                env_vars['GYP_MSVS_VERSION'] = {'7': '2003',
                                                '8': '2005',
                                                '9': '2008',
                                                '10': '2010',
                                                '11': '2012',
                                                '12': '2013',
                                                '14': '2015',
                                                '15': '2017'}.get(str(self.settings.compiler.version))
            with tools.environment_append(env_vars):
                target_arch = {'x86': 'ia32', 'x86_64': 'x64'}.get(str(self.settings.arch))
                uv_library = 'shared_library' if self.options.shared else 'static_library'
                self.run('python gyp_uv.py -f ninja -Dtarget_arch=%s -Duv_library=%s' % (target_arch, uv_library))
                self.run('ninja -C out/%s' % self.settings.build_type)

    def build_old(self):
        if self.settings.os == "Windows":
            with tools.chdir(self.root):
                tools.replace_in_file("vcbuild.bat", ":run", "exit /b 0")
                tools.replace_in_file("vcbuild.bat", "set target=Build", "set target=libuv")
                vcbuild_args = [str(self.settings.build_type).lower()]
                vcbuild_args.append("x64" if self.settings.arch == "x86_64" else "x86")
                vcbuild_args.append("shared" if self.options.shared else "static")
                if self.options["compiler"].version == "15":
                    vcbuild_args.append("vs2017")
                self.run("vcbuild.bat %s" % ' '.join(vcbuild_args))
        else:
            env_build = AutoToolsBuildEnvironment(self)
            with tools.chdir(self.root):
                self.run("./autogen.sh")
                configure_args = ['--prefix=%s' % self.install_dir]
                configure_args.append("--enable-shared" if self.options.shared else "--disable-shared")
                env_build.configure(args=configure_args)
                env_build.fpic = True
                env_build.make(args=["all"])
                env_build.make(args=["install"])

    def package(self):
        self.copy(pattern="*.h", dst="include", src=os.path.join(self.root, 'include'))
        bin_dir = os.path.join(self.root, 'out', str(self.settings.build_type))
        if self.settings.os == "Windows":
            if self.options.shared:
                self.copy(pattern="*.dll", dst="bin", src=bin_dir, keep_path=False)
            self.copy(pattern="*.lib", dst="lib", src=bin_dir, keep_path=False)

    def package_old(self):
        self.copy(pattern="LICENSE", dst=".", src=os.path.join(self.root, "LICENSE"))
        include_dir = self.install_dir if self.settings.os == "Linux" else self.root
        self.copy(pattern="*.h", dst="include", src=os.path.join(include_dir, "include"))
        if self.settings.os != "Windows":
            self.copy(pattern="*.pc", dst="res", src=os.path.join(self.install_dir, "lib"))
            self.copy(pattern="*.la", dst="lib", src=os.path.join(self.install_dir, "lib"), keep_path=False)
        if self.options.shared:
            if self.settings.os == "Windows":
                self.copy(pattern="*.dll", dst="bin", src=os.path.join(self.root, str(self.settings.build_type)), keep_path=False)
                self.copy(pattern="libuv.pdb", dst="lib", src=os.path.join(self.root, str(self.settings.build_type)), keep_path=False)
                self.copy(pattern="libuv.lib", dst="lib", src=os.path.join(self.root, str(self.settings.build_type)), keep_path=False)
            elif self.settings.os == "Linux":
                self.copy(pattern="*.so*", dst="lib", src=os.path.join(self.install_dir, "lib"), keep_path=False)
            elif self.settings.os == "Macos":
                self.copy(pattern="*.dylib", dst="lib", src=os.path.join(self.install_dir, "lib"), keep_path=False)
        else:
            if self.settings.os == "Windows":
                self.copy(pattern="*.lib", dst="lib", src=os.path.join(self.root, str(self.settings.build_type), "lib"), keep_path=False)
            else:
                self.copy(pattern="*.a", dst="lib", src=os.path.join(self.install_dir, "lib"), keep_path=False)

    def package_info(self):
        if self.options.shared:
            self.cpp_info.libs = ['libuv.dll.lib']
        else:
            self.cpp_info.libs = ['libuv']
        if self.settings.os == "Linux":
            self.cpp_info.libs.append("pthread")
        elif self.settings.os == "Windows":
            self.cpp_info.libs.extend(["Psapi", "Ws2_32", "Iphlpapi", "Userenv"])
