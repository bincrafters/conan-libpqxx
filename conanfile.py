import os
from conans import ConanFile, CMake, AutoToolsBuildEnvironment, tools
from conans.tools import os_info, SystemPackageTool, download, untargz, replace_in_file, unzip


class LibpqxxConan(ConanFile):
    name = "libpqxx"
    version = "5.0.1"
    settings = "os", "compiler", "build_type", "arch"
    description = "Conan package for the libpqxx library"
    url = "https://github.com/jgsogo/conan-libpqxx"
    license = "https://github.com/jtv/libpqxx/blob/master/COPYING"
    options = {"disable_documentation": [True, False],}
    default_options = "disable_documentation=True"

    def system_requirements(self):
        if os_info.is_linux:
            if os_info.with_apt:
                installer = SystemPackageTool()
                installer.install("libpq-dev")
                if not self.options.disable_documentation:
                    installer.install("doxygen")

    def source(self):
        if self.version == 'master':
            raise NotImplementedError("Compilation of master branch not implemented")
        else:
            url = "https://github.com/jtv/libpqxx/archive/{}.tar.gz".format(self.version)
            zip_name = 'libpqxx.tar.gz'
            download(url, zip_name)
            untargz(zip_name)
            os.unlink(zip_name)

    def build(self):
        if self.settings.os == "Linux" or self.settings.os == "Macos":

            options = "--disable-documentation"
            if not self.options.disable_documentation:
                options = ""

            env = AutoToolsBuildEnvironment(self)
            with tools.environment_append(env.vars):
                command = './configure {} && make'.format(options)
                self.run("cd libpqxx-%s && %s" % (self.version, command))
        else:
            raise NotImplementedError("Compilation of master branch not implemented")

    def package(self):
        source_folder = "libpqxx-{}".format(self.version)
        self.copy("pqxx/*", dst="include", src=os.path.join(source_folder, "include"), keep_path=True)
        self.copy(pattern="COPYING", dst="licenses", src=source_folder, ignore_case=True, keep_path=False)

        if self.settings.os == "Linux":
            # if shared:
            # self.copy(pattern="*.so*", dst="lib", src=os.path.join(self.FOLDER_NAME, "lib", ".libs"))
            self.copy("*.a", dst="lib", src=os.path.join(source_folder, "src", ".libs"))


    def package_info(self):
        self.cpp_info.libs = ["pqxx", "pq"]
