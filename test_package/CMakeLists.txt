project(LibpqxxConanTest)
cmake_minimum_required(VERSION 3.1 FATAL_ERROR)

set(CMAKE_CXX_STANDARD 11)
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(libpqxx_test main.cpp)
target_link_libraries(libpqxx_test PUBLIC "${CONAN_LIBS}")
set_target_properties(libpqxx_test PROPERTIES LINK_FLAGS "${CONAN_EXE_LINKER_FLAGS}")

