cmake_minimum_required(VERSION 3.1.2)
project(conan-libpqxx)

include(conanbuildinfo.cmake)
conan_basic_setup()

if (WIN32)
    add_definitions(-DWIN32 -D_MBCS -D_WINDOWS -DPQXX_INTERNAL -DNOMINMAX)
endif()

add_subdirectory(source_subfolder)

if (BUILD_SHARED_LIBS AND WIN32)
    # Fixes build missing Windows DLL entry point: https://github.com/jtv/libpqxx/pull/167
    target_sources(pqxx_shared PRIVATE "${CMAKE_SOURCE_DIR}/source_subfolder/win32/libpqxx.cxx")
endif()
