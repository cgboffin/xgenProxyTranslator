project(xgenProxyTranslator)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/modules)
FIND_PACKAGE( Maya REQUIRED )
FIND_PACKAGE( MtoA REQUIRED )
FIND_PACKAGE( Arnold REQUIRED )
FIND_PACKAGE( Xgen REQUIRED )

set(SOURCE_FILES "xgenProxyTranslator.cpp" "xgenProxyTranslator.h" "xgenProxyTranslator.py")

INCLUDE_DIRECTORIES( ${PUBLIC_INCLUDE_DIRS} ${MAYA_INCLUDE_DIR} ${MTOA_INCLUDE_DIR} ${ARNOLD_INCLUDE_DIR})

# create the plugin
add_library(xgenProxyTranslator SHARED ${SOURCE_FILES})

target_link_libraries(xgenProxyTranslator PRIVATE MtoA::MtoA Maya::Maya Arnold::Arnold Xgen::Xgen)
target_include_directories(xgenProxyTranslator PRIVATE MtoA::MtoA Maya::Maya Arnold::Arnold Xgen::Xgen)

MTOA_PLUGIN(xgenProxyTranslator)
