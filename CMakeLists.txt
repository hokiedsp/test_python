cmake_minimum_required(VERSION 3.5)
project(python_cpp_example)

# configure pybind & catch2
add_subdirectory("lib/pybind11")
add_subdirectory("lib/catch2")
list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/lib/catch2/contrib")

add_subdirectory("src")
add_subdirectory("tests")
enable_testing()
