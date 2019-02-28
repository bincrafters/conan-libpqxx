cmake_minimum_required(VERSION 3.1.2)
project(conan-libpqxx)

include(conanbuildinfo.cmake)
conan_basic_setup()

add_subdirectory(source_subfolder)

if (BUILD_SHARED_LIBS AND WIN32)
    # Fixes build missing Windows DLL entry point: https://github.com/jtv/libpqxx/pull/167
    target_sources(pqxx_shared PRIVATE "${CMAKE_SOURCE_DIR}/source_subfolder/win32/libpqxx.cxx")
endif()

if (WIN32)
    target_compile_definitions(${PROJECT_NAME} PUBLIC WIN32 _MBCS _WINDOWS PQXX_INTERNAL NOMINMAX)
endif()
