cmake_minimum_required(VERSION 3.7)
project(libpqxx)

include(conanbuildinfo.cmake)
conan_basic_setup()

find_package(PostgreSQL REQUIRED)

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
set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 14)

install(TARGETS ${PROJECT_NAME}
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib)

install(DIRECTORY "${CMAKE_SOURCE_DIR}/source_subfolder/include" DESTINATION "${CMAKE_INSTALL_PREFIX}")
install(DIRECTORY "${CMAKE_BINARY_DIR}/include" DESTINATION "${CMAKE_INSTALL_PREFIX}")
