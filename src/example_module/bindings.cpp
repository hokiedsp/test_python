#include <pybind11/pybind11.h>
#include "math.hpp"

namespace py = pybind11;

PYBIND11_MODULE(python_cpp_example, m)
{
  m.doc() = R"doc(
        Python module
        -----------------------
        .. currentmodule:: python_cpp_example
        .. autosummary::
           :toctree: _generate
           
           add
           subtract
    )doc";

  m.def("add", &add, R"doc(
        Add two numbers
        
        Some other information about the add function.
    )doc");

  m.def("subtract", &subtract, R"doc(
        Subtract two numbers

        Some other information about the subtract function.
    )doc");
}
