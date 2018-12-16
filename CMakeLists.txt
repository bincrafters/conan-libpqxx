cmake_minimum_required(VERSION 3.1.2)
project(libpqxx VERSION 6.2.4 LANGUAGES CXX)

include(conanbuildinfo.cmake)
conan_basic_setup()

find_package(PostgreSQL REQUIRED)

include(CheckIncludeFileCXX)

check_include_file_cxx(poll.h HAVE_POLL)
check_include_file_cxx(sys/select.h HAVE_SYS_SELECT_H)
check_include_file_cxx(sys/time.h HAVE_SYS_TIME_H)
check_include_file_cxx(sys/types.h HAVE_SYS_TYPES_H)
check_include_file_cxx(unistd.h HAVE_UNISTD_H)

include(CheckCXXSourceCompiles)

check_cxx_source_compiles("[[deprecated]] void f();
int main() { return 0; }" PQXX_HAVE_DEPRECATED)
check_cxx_source_compiles("#include <optional>
int main() { return std::optional<int>(0).value(); }" PQXX_HAVE_OPTIONAL)
check_cxx_source_compiles("#include <experimental/optional>
int main() { return std::experimental::optional<int>(0).value(); }" PQXX_HAVE_EXP_OPTIONAL)

set(AC_CONFIG_H_IN "${CMAKE_SOURCE_DIR}/include/pqxx/config.h.in")
set(CM_CONFIG_H_IN "${CMAKE_BINARY_DIR}/include/pqxx/config.h.in")
set(CM_CONFIG_PUB "${CMAKE_BINARY_DIR}/include/pqxx/config-public-compiler.h")
set(CM_CONFIG_INT "${CMAKE_BINARY_DIR}/include/pqxx/config-internal-compiler.h")

file(WRITE "${CM_CONFIG_H_IN}" "")
file(STRINGS "${AC_CONFIG_H_IN}" lines)

foreach (line ${lines})
  string(REGEX REPLACE "^#undef" "#cmakedefine" l "${line}")
  file(APPEND "${CM_CONFIG_H_IN}" "${l}\n")
endforeach (line)

configure_file("${CM_CONFIG_H_IN}" "${CM_CONFIG_INT}" @ONLY)
configure_file("${CM_CONFIG_H_IN}" "${CM_CONFIG_PUB}" @ONLY)

file(GLOB CXX_SOURCES "${CMAKE_SOURCE_DIR}/source_subfolder/src/*.cxx")
if (BUILD_SHARED_LIBS AND WIN32)
    list(APPEND CXX_SOURCES "${CMAKE_SOURCE_DIR}/source_subfolder/win32/libpqxx.cxx")
endif()

add_library(${PROJECT_NAME} ${CXX_SOURCES})
if (BUILD_SHARED_LIBS)
    target_compile_definitions(${PROJECT_NAME} PUBLIC -DPQXX_SHARED)
endif()

if (WIN32)
    target_compile_definitions(${PROJECT_NAME} PUBLIC WIN32 _MBCS _WINDOWS PQXX_INTERNAL NOMINMAX)
endif()

target_include_directories(${PROJECT_NAME} PUBLIC "${CMAKE_SOURCE_DIR}/source_subfolder/include" "${PostgreSQL_INCLUDE_DIRS}")
target_include_directories(${PROJECT_NAME} PRIVATE "${CMAKE_BINARY_DIR}/include")

target_link_libraries(${PROJECT_NAME} PUBLIC ${PostgreSQL_LIBRARIES})
if (WIN32)
    target_link_libraries(${PROJECT_NAME} PRIVATE ws2_32)
endif()

set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 14)
if (WIN32 AND MSVC AND BUILD_SHARED_LIBS)
    set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS ON)
endif()

install(TARGETS ${PROJECT_NAME}
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib)

install(DIRECTORY "${CMAKE_SOURCE_DIR}/source_subfolder/include"
        DESTINATION "${CMAKE_INSTALL_PREFIX}"
        PATTERN "doc" EXCLUDE
        PATTERN "*.md" EXCLUDE
        PATTERN "*.in" EXCLUDE
        PATTERN "*.am" EXCLUDE
        PATTERN "*.template" EXCLUDE)

install(DIRECTORY "${CMAKE_BINARY_DIR}/include"
        DESTINATION "${CMAKE_INSTALL_PREFIX}"
        FILES_MATCHING PATTERN "*.h")
