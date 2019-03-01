#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from conans import ConanFile, tools, AutoToolsBuildEnvironment, CMake
from conans.model.version import Version
from conans.errors import ConanInvalidConfiguration


class LibpqxxRecipe(ConanFile):
    name = "libpqxx"
    version = "6.3.1"
    settings = "os", "compiler", "build_type", "arch", "cppstd"
    description = "The official C++ client API for PostgreSQL"
    url = "https://github.com/bincrafters/conan-libpqxx"
    homepage = "https://github.com/jtv/libpqxx"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "BSD-3-Clause"
    topics = ("conan", "libpqxx", "postgres", "postgresql", "data-base")
    generators = "cmake"
    exports = "LICENSE.md"
    exports_sources = "CMakeLists.txt"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    requires = "libpq/9.6.9@bincrafters/stable"
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    _autotools = None

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.remove("fPIC")

    def configure(self):
        compiler_version = Version(self.settings.compiler.version.value)

        if self.settings.os == "Windows" and \
           self.settings.compiler == "Visual Studio" and \
           compiler_version < "14":
            raise ConanInvalidConfiguration("Your MSVC version is too old, libpqxx requires C++14")

        if self.settings.os == "Macos" and \
           self.settings.compiler == "apple-clang" and \
           compiler_version < "8.0":
            raise ConanInvalidConfiguration(("libpqxx requires thread-local storage features,"
                                             " could not be built by apple-clang < 8.0"))

    def source(self):
        sha256 = "00975df6d8e5a06060c232c7156ec63a2b0b8cbb097b6ac7833fa9e48f50d0ed"
        tools.get("{0}/archive/{1}.tar.gz".format(self.homepage, self.version), sha256=sha256)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

        # Fixes build errors with gcc 4.9: https://github.com/jtv/libpqxx/issues/161
        tools.replace_in_file(
            os.path.join(self._source_subfolder, "src", "encodings.cxx"),
            "auto found_encoding_group{encoding_map.find(encoding_name)};",
            "const auto found_encoding_group = encoding_map.find(encoding_name);")

        # Fixes install missing config-compiler-public.h: https://github.com/jtv/libpqxx/pull/169/files
        tools.replace_in_file(
            os.path.join(self._source_subfolder, "include", "CMakeLists.txt"),
            "DIRECTORY pqxx", 'DIRECTORY pqxx "${PROJECT_BINARY_DIR}/include/pqxx"')

    def _configure_autotools(self):
        if not self._autotools:
            args = [
                "--disable-documentation",
                "--with-postgres-include={}".format(os.path.join(self.deps_cpp_info["libpq"].rootpath, "include")),
                "--with-postgres-lib={}".format(os.path.join(self.deps_cpp_info["libpq"].rootpath, "lib")),
                "--enable-static={}".format("no" if self.options.shared else "yes"),
                "--enable-shared={}".format("yes" if self.options.shared else "no")
            ]
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            env_vars = self._autotools.vars
            env_vars["PG_CONFIG"] = os.path.join(self.deps_cpp_info["libpq"].rootpath, "bin", "pg_config")
            self._autotools.configure(args=args, vars=env_vars)
        return self._autotools

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["SKIP_BUILD_TEST"] = "ON"
        cmake.definitions["SKIP_PQXX_STATIC"] = "ON" if self.options.shared else "OFF"
        cmake.definitions["SKIP_PQXX_SHARED"] = "OFF" if self.options.shared else "ON"
        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        if self.settings.os == "Windows":
            cmake = self._configure_cmake()
            cmake.build()
        else:
            with tools.chdir(self._source_subfolder):
                autotools = self._configure_autotools()
                autotools.make()

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        if self.settings.os == "Windows":
            cmake = self._configure_cmake()
            cmake.install()

            # Fixes install missing header include/pqxx/pqxx: https://github.com/jtv/libpqxx/issues/166
            self.copy("pqxx", dst="include/pqxx",
                      src=os.path.join(self._source_subfolder, "include", "pqxx"))

        else:
            with tools.chdir(self._source_subfolder):
                autotools = self._configure_autotools()
                autotools.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.libs.append("Ws2_32")
        elif self.settings.os == "Linux":
            self.cpp_info.libs.append("pthread")
