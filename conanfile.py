import os
import shutil
from conans import ConanFile, CMake, AutoToolsBuildEnvironment, tools, VisualStudioBuildEnvironment
from conans.tools import os_info, SystemPackageTool, download, untargz, replace_in_file, unzip


class LibpqxxConan(ConanFile):
    name = "libpqxx"
    version = "5.0.1"
    settings = "os", "compiler", "build_type", "arch"
    description = "Conan package for the libpqxx library"
    url = "https://github.com/jgsogo/conan-libpqxx"
    license = "https://github.com/jtv/libpqxx/blob/master/COPYING"
    options = {"disable_documentation": [True, False],
               "shared": [True, False], }
    default_options = "disable_documentation=True", "shared=False"

    @property
    def source_dir(self):
        return os.path.abspath("libpqxx-%s" % self.version)

    def system_requirements(self):
        if os_info.is_linux:
            if os_info.with_apt:
                installer = SystemPackageTool()
                installer.install("libpq-dev")
                if not self.options.disable_documentation:
                    installer.install("doxygen")

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.build_requires("postgresql/v9.6.5@jgsogo/stable")
                
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
                self.run("cd %s && %s" % (self.source_dir, command))
        else:
            self.windows_build()

    def package(self):
        self.copy("pqxx/*", dst="include", src=os.path.join(self.source_dir, "include"), keep_path=True)
        self.copy(pattern="COPYING", dst="licenses", src=self.source_dir, ignore_case=True, keep_path=False)

        if self.settings.os == "Linux":
            # if shared:
            # self.copy(pattern="*.so*", dst="lib", src=os.path.join(self.FOLDER_NAME, "lib", ".libs"))
            self.copy("*.a", dst="lib", src=os.path.join(self.source_dir, "src", ".libs"))
        elif self.settings.os == "Windows":
            self.copy("*.lib", dst="lib", src=os.path.join(self.source_dir, "lib"))
            self.copy("*.bin", dst="bin", src=os.path.join(self.source_dir, "lib"))

    def package_info(self):
        if self.settings.os == "Linux":
            self.cpp_info.libs = ["pqxx", "pq"]
        elif self.settings.os == "Windows":
            base_name = "libpqxx"
            if not self.options.shared:
                base_name += "_static"
            self.cpp_info.libs = [base_name, ]

    def windows_build(self):
        # Follow instructions in https://github.com/jtv/libpqxx/blob/master/win32/INSTALL.txt
        common_file = os.path.join(self.source_dir, 'win32', 'common')
        with open(common_file, "w") as f:
            f.write('PGSQLSRC="{}"'.format(self.deps_cpp_info["postgresql"].rootpath))
            f.write('PGSQLINC=$(PGSQLSRC)\include')
            f.write('LIBPQINC=$(PGSQLSRC)\include')

            f.write('LIBPQPATH=$(PGSQLSRC)\lib')
            f.write('LIBPQDLL=libpq.dll')
            f.write('LIBPQLIB=libpq.lib')

            f.write('LIBPQDPATH=$(PGSQLSRC)\lib')
            f.write('LIBPQDDLL=libpq.dll')
            f.write('LIBPQDLIB=libpq.lib')

        target_dir = os.path.join(self.source_dir, 'include', 'pqxx')
        with tools.chdir(os.path.join(self.source_dir, 'config', 'sample-headers', 'compiler', 'VisualStudio2013', 'pqxx')):
            shutil.copy('config-internal-compiler.h', target_dir + "/")
            shutil.copy('config-public-compiler.h', target_dir + "/")

        vcvars = tools.vcvars_command(self.settings)
        env = VisualStudioBuildEnvironment(self)
        with tools.environment_append(env.vars):
            with tools.chdir(self.source_dir):
                target = "DLL" if self.options.shared else "STATIC"
                target += str(self.settings.build_type).upper()
                command = '%s && nmake /f win32/vc-libpqxx.mak %s' % (vcvars, target)
                self.output.info(command)
                self.run(command)
