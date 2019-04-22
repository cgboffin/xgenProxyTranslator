# MTOA_FOUND            set if MtoA is found.
# MTOA_INCLUDE_DIR      MtoA's include directory
# MTOA_mtoa_api_LIBRARY Full path location of libmtoa_api
# MTOA_LIBRARY          Alias for MTOA_mtoa_api_LIBRARY

find_package(PackageHandleStandardArgs)
if(NOT DEFINED MTOA_VERSION)
    set(MTOA_VERSION 2017 CACHE STRING "MtoA version")
endif()
set(MTOA_INSTALL_BASE_PATH "C:/solidangle/mtoadeploy")
set(MTOA_ROOT_LOCATION ${MTOA_INSTALL_BASE_PATH}/${MTOA_VERSION})


# MtoA include directory
find_path(MTOA_INCLUDE_DIR extension/Extension.h
    PATHS
        ${MTOA_ROOT_LOCATION}
        $ENV{MTOA_ROOT_LOCATION}
    PATH_SUFFIXES
        "include/"
)

find_library(MTOA_LIBRARY
    NAMES 
        mtoa_api
    PATHS
        ${MTOA_ROOT_LOCATION}
        $ENV{MTOA_ROOT_LOCATION}
    PATH_SUFFIXES
        "lib/"
    NO_DEFAULT_PATH
)

set(MTOA_COMPILE_DEFINITIONS "REQUIRE_IOSTREAM;_BOOL")
set(MTOA_COMPILE_DEFINITIONS "${MTOA_COMPILE_DEFINITIONS};NT_PLUGIN")

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(MtoA
    REQUIRED_VARS MTOA_INCLUDE_DIR MTOA_LIBRARY)
mark_as_advanced(MTOA_INCLUDE_DIR MTOA_LIBRARY)

if (NOT TARGET MtoA::MtoA)
    add_library(MtoA::MtoA UNKNOWN IMPORTED)
    set_target_properties(MtoA::MtoA PROPERTIES
        INTERFACE_COMPILE_DEFINITIONS "${MTOA_COMPILE_DEFINITIONS}"
        INTERFACE_INCLUDE_DIRECTORIES "${MTOA_INCLUDE_DIR}"
        IMPORTED_LOCATION "${MTOA_LIBRARY}")
endif()

set(MTOA_PLUGIN_EXTENSION ".dll")
function(MTOA_PLUGIN _target)
    set_target_properties(${_target} PROPERTIES
        PREFIX ""
        SUFFIX ${MTOA_PLUGIN_EXTENSION})
endfunction()