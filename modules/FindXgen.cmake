# - Maya finder module
if(NOT DEFINED MAYA_LOCATION)
    # Set a default Maya version if not specified
    if(NOT DEFINED MAYA_VERSION)
        set(MAYA_VERSION 2017 CACHE STRING "Maya version")
    endif()
 
    # OS Specific environment setup
    set(MAYA_INSTALL_BASE_SUFFIX "")
    if(WIN32)
        # Windows
        set(MAYA_INSTALL_BASE_DEFAULT "C:/Program Files/Autodesk")
    elseif(APPLE)
        # Apple
        set(MAYA_INSTALL_BASE_DEFAULT /Applications/Autodesk)
    else()
        # Linux
        set(MAYA_INSTALL_BASE_DEFAULT /usr/autodesk)
        if(MAYA_VERSION LESS 2016)
            SET(MAYA_INSTALL_BASE_SUFFIX -x64)
        endif()
    endif()
     
    set(MAYA_INSTALL_BASE_PATH ${MAYA_INSTALL_BASE_DEFAULT} CACHE STRING
        "Root path containing your maya installations, e.g. /usr/autodesk or /Applications/Autodesk/")
     
    set(MAYA_LOCATION ${MAYA_INSTALL_BASE_PATH}/maya${MAYA_VERSION}${MAYA_INSTALL_BASE_SUFFIX})
endif()
 
 
# OS Specific environment setup
set(XGEN_PLUGIN_BASE_PATH "${MAYA_LOCATION}/plug-ins/xgen")
if(WIN32)
    # Windows
    set(XGENLIB libAdskXGen.lib)
elseif(APPLE)
    # Apple
    set(XGENLIB libAdskXGen.dylib)
else()
    # Linux
    set(XGENLIB libAdskXGen.so)
endif()
 
# XGen library directory
find_library(XGEN_LIBRARY
    NAMES 
        libAdskXGen
    PATHS
        ${XGEN_PLUGIN_BASE_PATH}
        $ENV{XGEN_PLUGIN_BASE_PATH}
    PATH_SUFFIXES
        "lib/"
    NO_DEFAULT_PATH
)
set(XGEN_LIBRARIES "${XGEN_LIBRARY}")
 
# XGen include directory
find_path(XGEN_DIR XgObject.h
    PATHS
        ${XGEN_PLUGIN_BASE_PATH}/include
    PATH_SUFFIXES
        "XGen/"
    DOC "XGen include path"
)
 
# SeExpr include directory
find_path(SEEXPR_DIR SeExpression.h
    PATHS
        ${XGEN_PLUGIN_BASE_PATH}/include
    PATH_SUFFIXES
        "SeExpr/"
    DOC "SeExpr include path"
)

# XgPorting include directory
find_path(XGPORTING_DIR safevector.h
    PATHS
        ${XGEN_PLUGIN_BASE_PATH}/include
    PATH_SUFFIXES
        "XgPorting/"
    DOC "XgPorting include path"
)

# Maya include directory
if(NOT DEFINED MAYA_LIBRARY)
    find_library(MAYA_LIBRARY
        NAMES 
            OpenMaya
        PATHS
            ${MAYA_LOCATION}
            $ENV{MAYA_LOCATION}
        PATH_SUFFIXES
            "lib/"
        NO_DEFAULT_PATH
    )
endif()

# Maya include directory
if(NOT DEFINED MAYA_INCLUDE_DIR)
    # Maya include directory
    find_path(MAYA_INCLUDE_DIR maya/MFn.h
        PATHS
            ${MAYA_LOCATION}
            $ENV{MAYA_LOCATION}
        PATH_SUFFIXES
            "include/"
            "devkit/include/"
    )
endif()

set(XGEN_COMPILE_DEFINITIONS "REQUIRE_IOSTREAM;_BOOL")
set(XGEN_COMPILE_DEFINITIONS "${XGEN_COMPILE_DEFINITIONS};NT_PLUGIN")
set(XGEN_INCLUDE_DIR "${XGEN_PLUGIN_BASE_PATH}/include" "${MAYA_INCLUDE_DIR}" "${XGEN_DIR}" "${XGPORTING_DIR}" "${SEEXPR_DIR}")

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Xgen
    REQUIRED_VARS XGEN_INCLUDE_DIR XGEN_DIR SEEXPR_DIR XGPORTING_DIR MAYA_INCLUDE_DIR)
mark_as_advanced(XGEN_INCLUDE_DIR XGEN_LIBRARY)

if (NOT TARGET Xgen::Xgen)
    add_library(Xgen::Xgen UNKNOWN IMPORTED)
    set_target_properties(Xgen::Xgen PROPERTIES
        INTERFACE_COMPILE_DEFINITIONS "${XGEN_COMPILE_DEFINITIONS}"
        INTERFACE_INCLUDE_DIRECTORIES "${XGEN_INCLUDE_DIR}"
        IMPORTED_LOCATION "${XGEN_LIBRARY}")
endif()

# Xgen libraries
set(_XGEN_LIBRARIES libAdskSeExpr libAdskXGen libAdskXpd tbb)
foreach(XGEN_LIB ${_XGEN_LIBRARIES})
    find_library(XGEN_${XGEN_LIB}_LIBRARY
        NAMES 
            ${XGEN_LIB}
        PATHS
            ${XGEN_PLUGIN_BASE_PATH}
            ${MAYA_LOCATION}
            $ENV{MAYA_LOCATION}
        PATH_SUFFIXES
            "lib/"
        NO_DEFAULT_PATH)
    mark_as_advanced(XGEN_${XGEN_LIB}_LIBRARY)
    if (XGEN_${XGEN_LIB}_LIBRARY)
        message(STATUS XGEN_${XGEN_LIB}_LIBRARY)
        add_library(Xgen::${XGEN_LIB} UNKNOWN IMPORTED)
        set_target_properties(Xgen::${XGEN_LIB} PROPERTIES
            IMPORTED_LOCATION "${XGEN_${XGEN_LIB}_LIBRARY}")
        set_property(TARGET Xgen::Xgen APPEND PROPERTY
            INTERFACE_LINK_LIBRARIES Xgen::${XGEN_LIB})
        set(XGEN_LIBRARIES ${XGEN_LIBRARIES} "${XGEN_${XGEN_LIB}_LIBRARY}")
    endif()
endforeach()

set(XGEN_PLUGIN_EXTENSION ".dll")
function(MAYA_XGEN_PLUGIN _target)
    set_target_properties(${_target} PROPERTIES
        PREFIX ""
        SUFFIX ${XGEN_PLUGIN_EXTENSION})
endfunction()