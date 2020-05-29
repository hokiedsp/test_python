# Generate pybind python module
SET(TARGET "python_cpp_example")
LIST(APPEND SOURCES "math.cpp" "bindings.cpp")
pybind11_add_module(${TARGET} ${SOURCES})

# install py & pyd files to matching subdirectory in dist
file(RELATIVE_PATH DST_DIR ${SRC_DIR} ${CMAKE_CURRENT_SOURCE_DIR})
install(TARGETS ${TARGET} DESTINATION ${DST_DIR})
file(GLOB PYFILES LIST_DIRECTORIES false RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} "*.py")
install(FILES ${PYFILES} DESTINATION ${DST_DIR}) # copy all the py-files in dir
