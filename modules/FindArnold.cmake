#ARNOLD_FOUND            set if Arnold is found.
#ARNOLD_INCLUDE_DIR      Arnold's include directory
#ARNOLD_mtoa_api_LIBRARY Full path location of libmtoa_api
#ARNOLD_LIBRARY          Alias forARNOLD_mtoa_api_LIBRARY

find_package(PackageHandleStandardArgs)
if(NOT DEFINEDARNOLD_VERSION)
    set(ARNOLD_VERSION 4.2.14 CACHE STRING "Arnold version")
endif()
set(ARNOLD_INSTALL_BASE_PATH "C:/solidangle/arnoldcore")
set(ARNOLD_ROOT_LOCATION ${ARNOLD_INSTALL_BASE_PATH}/${ARNOLD_VERSION})


# Arnold include directory
find_path(ARNOLD_INCLUDE_DIR ai.h
    PATHS
        ${ARNOLD_ROOT_LOCATION}
        $ENV{ARNOLD_ROOT_LOCATION}
    PATH_SUFFIXES
        "include/"
)

find_library(ARNOLD_LIBRARY
    NAMES 
       ai
    PATHS
        ${ARNOLD_ROOT_LOCATION}
        $ENV{ARNOLD_ROOT_LOCATION}
    PATH_SUFFIXES
        "lib/"
    NO_DEFAULT_PATH
)

set(ARNOLD_COMPILE_DEFINITIONS "REQUIRE_IOSTREAM;_BOOL")
set(ARNOLD_COMPILE_DEFINITIONS "${ARNOLD_COMPILE_DEFINITIONS};NT_PLUGIN")

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Arnold
    REQUIRED_VARSARNOLD_INCLUDE_DIRARNOLD_LIBRARY)
mark_as_advanced(ARNOLD_INCLUDE_DIRARNOLD_LIBRARY)

if (NOT TARGET Arnold::Arnold)
    add_library(Arnold::Arnold UNKNOWN IMPORTED)
    set_target_properties(Arnold::Arnold PROPERTIES
        INTERFACE_COMPILE_DEFINITIONS "${ARNOLD_COMPILE_DEFINITIONS}"
        INTERFACE_INCLUDE_DIRECTORIES "${ARNOLD_INCLUDE_DIR}"
        IMPORTED_LOCATION "${ARNOLD_LIBRARY}")
endif()

set(ARNOLD_PLUGIN_EXTENSION ".dll")
function(ARNOLD_PLUGIN _target)
    set_target_properties(${_target} PROPERTIES
        PREFIX ""
        SUFFIX ${ARNOLD_PLUGIN_EXTENSION})
endfunction()