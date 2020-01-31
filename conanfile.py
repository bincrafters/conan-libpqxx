import os
from conans import ConanFile, tools, AutoToolsBuildEnvironment, CMake
from conans.tools import Version
from conans.errors import ConanInvalidConfiguration


class LibpqxxRecipe(ConanFile):
    name = "libpqxx"
    version = "7.0.0"
    settings = "os", "compiler", "build_type", "arch"
    description = "The official C++ client API for PostgreSQL"
    url = "https://github.com/bincrafters/conan-libpqxx"
    homepage = "https://github.com/jtv/libpqxx"
    license = "BSD-3-Clause"
    topics = ("conan", "libpqxx", "postgres", "postgresql", "data-base")
    generators = "cmake"
    exports = "LICENSE.md"
    exports_sources = "CMakeLists.txt"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    requires = "libpq/9.6.9@bincrafters/stable"
    _autotools = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.remove("fPIC")

    def configure(self):
        compiler = str(self.settings.compiler)
        compiler_version = Version(self.settings.compiler.version.value)

        minimal_version = {
            "Visual Studio": "15",
            "gcc": "7",
            "clang": "6",
            "apple-clang": "9"
        }

        if compiler in minimal_version and \
           compiler_version < minimal_version[compiler]:
            raise ConanInvalidConfiguration("%s requires a compiler that supports"
                                            " at least C++17. %s %s is not"
                                            " supported." % (self.name, compiler, compiler_version))
        minimal_cpp_standard = "17"
        supported_cppstd = ["17", "20"]

        if not self.settings.compiler.cppstd:
            self.output.info("Settings c++ standard to {}".format(minimal_cpp_standard))
            self.settings.compiler.cppstd = minimal_cpp_standard

        if not self.settings.compiler.cppstd in supported_cppstd:
            raise ConanInvalidConfiguration(
                "%s requires a compiler that supports at least C++%s" % (self.name, minimal_cpp_standard))

    def source(self):
        sha256 = "7527bfde17a7123776fa0891f1b83273b32e1bc78dad7af1e893bd2b980ef882"
        tools.get("{0}/archive/{1}.tar.gz".format(self.homepage, self.version), sha256=sha256)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

        # Fix create symbolic link: https://github.com/jtv/libpqxx/issues/265
        # `cmake -E create_symlink` is not working if Windows 10 developer mode
        # is not enabled.
        # Remove `cmake -E create_symlink` command and reset install name of pqxx.
        tools.replace_in_file(
            os.path.join(self._source_subfolder, "src", "CMakeLists.txt"),
            """        add_custom_target(library_symlink ALL
        	${CMAKE_COMMAND} -E create_symlink
        		${library_prefix}${output_name}${library_suffix}
        		${library_prefix}${name}${library_suffix}
        )
        install(FILES ${CMAKE_CURRENT_BINARY_DIR}/${library_prefix}${name}${library_suffix}
        	DESTINATION ${CMAKE_INSTALL_LIBDIR}
        )""",
            """        set_property(TARGET ${tgt} PROPERTY OUTPUT_NAME)""")

        # Fix Visual Studio 2017 wrong compile error "C2397 narrowing conversion":
        tools.replace_in_file(
            os.path.join(self._source_subfolder, "src", "connection.cxx"),
            """void pqxx::connection::cancel_query()
{
  using pointer = std::unique_ptr<PGcancel, std::function<void(PGcancel *)>>;
  constexpr int buf_size{500};
  std::array<char, buf_size> errbuf;
  pointer cancel{PQgetCancel(m_conn), PQfreeCancel};
  if (cancel == nullptr)
    throw std::bad_alloc{};

  auto const c{PQcancel(cancel.get(), errbuf.data(), buf_size)};
  if (c == 0)
    throw pqxx::sql_error{std::string{errbuf.data(), buf_size}};
}""",
            """void pqxx::connection::cancel_query()
{
  using pointer = std::unique_ptr<PGcancel, std::function<void(PGcancel *)>>;
  constexpr int buf_size{500};
  std::array<char, buf_size> errbuf;
  pointer cancel{PQgetCancel(m_conn), PQfreeCancel};
  if (cancel == nullptr)
    throw std::bad_alloc{};

  auto const c{PQcancel(cancel.get(), errbuf.data(), buf_size)};
  if (c == 0)
    throw pqxx::sql_error{std::string{errbuf.data(), errbuf.size()}};
}""")

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
        cmake.definitions["BUILD_DOC"] = False
        cmake.definitions["BUILD_TEST"] = False
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
