#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from conans import ConanFile, AutoToolsBuildEnvironment, tools, VisualStudioBuildEnvironment


class LibpqxxRecipe(ConanFile):
    name = "libpqxx"
    version = "6.2.4"
    settings = "os", "compiler", "build_type", "arch"
    description = "The official C++ client API for PostgreSQL"
    url = "https://github.com/bincrafters/conan-libpqxx"
    homepage = "https://github.com/jtv/libpqxx"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "BSD-3"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = "shared=False", "fPIC=True"
    requires = "libpq/9.6.9@bincrafters/stable"
    source_subfolder = "source_subfolder"
    autotools = None

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.remove("fPIC")

    def source(self):
        tools.get("{0}/archive/{1}.tar.gz".format(self.homepage, self.version))
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_subfolder)

    def configure_autotools(self):
        if not self.autotools:
            self.autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            args = ["--disable-documentation"]
            args.append("--with-postgres-include={}".format(os.path.join(self.deps_cpp_info["libpq"].rootpath, "include")))
            args.append("--with-postgres-lib={}".format(os.path.join(self.deps_cpp_info["libpq"].rootpath, "lib")))
            with tools.chdir(self.source_subfolder):
                self.autotools.configure(args=args)
        return self.autotools

    def build(self):
        if self.settings.os == "Linux" or self.settings.os == "Macos":
            autotools = self.configure_autotools()
            with tools.chdir(self.source_subfolder):
                autotools.make()
        elif self.settings.os == "Windows":
            self.windows_build()
        else:
            raise Exception("Could not build: Platform {} is not supported.".format(self.settings.os))

    def package(self):
        self.copy(pattern="COPYING", dst="licenses", src=self.source_subfolder)
        if self.settings.os == "Linux":
            autotools = self.configure_autotools()
            with tools.chdir(self.source_subfolder):
                autotools.install()
        elif self.settings.os == "Windows":
            self.copy("*.lib", dst="lib", src=os.path.join(self.source_subfolder, "lib"))
            self.copy("*.bin", dst="bin", src=os.path.join(self.source_subfolder, "lib"))

    def package_info(self):
        if self.settings.os == "Linux":
            self.cpp_info.libs = tools.collect_libs(self)
        elif self.settings.os == "Windows":
            base_name = "libpqxx"
            if not self.options.shared:
                base_name += "_static"
            self.cpp_info.libs = [base_name, ]

    def windows_build(self):
        # Follow instructions in https://github.com/jtv/libpqxx/blob/master/win32/INSTALL.txt
        common_file = os.path.join(self.source_subfolder, 'win32', 'common')
        with open(common_file, "w") as f:
            f.write(b'PGSQLSRC="{}"\n'.format(self.deps_cpp_info["libpq"].rootpath))
            f.write(b'PGSQLINC=$(PGSQLSRC)\\include\n')
            f.write(b'LIBPQINC=$(PGSQLSRC)\\include\n')

            f.write(b'LIBPQPATH=$(PGSQLSRC)\\lib\n')
            f.write(b'LIBPQDLL=libpq.dll\n')
            f.write(b'LIBPQLIB=libpq.lib\n')

            f.write(b'LIBPQDPATH=$(PGSQLSRC)\\lib\n')
            f.write(b'LIBPQDDLL=libpq.dll\n')
            f.write(b'LIBPQDLIB=libpq.lib\n')

        target_dir = os.path.join(self.source_subfolder, 'include', 'pqxx')
        with tools.chdir(os.path.join(self.source_subfolder, 'config', 'sample-headers', 'compiler', 'VisualStudio2013', 'pqxx')):
            shutil.copy('config-internal-compiler.h', target_dir + "/")
            shutil.copy('config-public-compiler.h', target_dir + "/")

        vcvars = tools.vcvars_command(self.settings)
        self.run(vcvars)
        env = VisualStudioBuildEnvironment(self)
        with tools.environment_append(env.vars):
            with tools.chdir(self.source_subfolder):
                target = "DLL" if self.options.shared else "STATIC"
                target += str(self.settings.build_type).upper()
                command = 'nmake /f win32/vc-libpqxx.mak %s' % target
                self.output.info(command)
                self.run(command)
