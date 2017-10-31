import os
from os import path
import tempfile
from conans import ConanFile, AutoToolsBuildEnvironment, tools


class LibuvConan(ConanFile):
    name = "libuv"
    version = "1.15.0"
    settings = "os", "arch", "compiler", "build_type"
    generators = "cmake"
    options = {"shared": [True, False]}
    default_options = "shared=True"
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

    def build(self):
        env_build = AutoToolsBuildEnvironment(self)
        with tools.chdir(self.root):
            self.run("./autogen.sh")
            configure_args = ['--prefix=%s' % self.install_dir]
            env_build.configure(args=configure_args)
            env_build.fpic = True
            env_build.make(args=["all"])
            env_build.make(args=["install"])

    def package(self):
        self.copy(pattern="LICENSE", dst=".", src=path.join(self.root, "LICENSE"))
        self.copy(pattern="*.h", dst="include", src=path.join(self.install_dir, "include"))
        self.copy(pattern="*.pc", dst="res", src=path.join(self.install_dir, "lib"))
        self.copy(pattern="*.la", dst="lib", src=path.join(self.install_dir, "lib"), keep_path=False)
        if self.options.shared:
            self.copy(pattern="*.so*", dst="lib", src=path.join(self.install_dir, "lib"), keep_path=False)
            self.copy(pattern="*.dll", dst="bin", src="bin", keep_path=False)
            self.copy(pattern="*.dylib", dst="lib", src=path.join(self.install_dir, "lib"), keep_path=False)
        else:
            self.copy(pattern="*.a", dst="lib", src=path.join(self.install_dir, "lib"), keep_path=False)
            self.copy(pattern="*.lib", dst="lib", src="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs =  tools.collect_libs(self)
