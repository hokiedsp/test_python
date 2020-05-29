#! /usr/bin/env python3

import os
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
from setuptools.command.test import test as TestCommand

# local module import
import cmakeutil

# path to the cmake executable (findexe("cmake") does auto-detection)
cmakePath = cmakeutil.findexe("cmake")

cmakeGenerator = "Ninja"
cmakeBuildDir = "build" # where to build C++ (absolute or relative to project dir)
cmakeForceConfigure = False  # True to re-configure each time; False to configure once
distDir = "dist"  # where to "install" the python package files (absolute or relative to project dir)


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)
        print("CMakeExtension", name, sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            cmakeutil.validate(cmakePath)
        except OSError:
            raise RuntimeError(
                "CMake must be installed to build the following extensions: "
                + ", ".join(e.name for e in self.extensions)
            )

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):

        env = os.environ.copy()

        buildType = "Debug" if self.debug else "Release"
        print(f"\nBuilding {buildType} configuration\n")

        hasCache = cmakeutil.configured(cmakeBuildDir)
        if cmakeForceConfigure and hasCache:
            print("\nRemoving previous CMake project configuration...\n\n")
            cmakeutil.clear(cmakeBuildDir)
            hasCache = False

        if not hasCache:
            print("\nConfiguring CMake project...\n\n")
            cmakeutil.configure(
                S=".",
                B=cmakeBuildDir,
                G=cmakeGenerator,
                D=[{"var": "CMAKE_BUILD_TYPE", "value": buildType, "type": "STRING"}],
                env=env,
            )

        print("\nBuilding CMake project...\n\n")
        cmakeutil.build(cmakeBuildDir, config=buildType, env=env)

        print("\nInstalling CMake project...\n\n")
        cmakeutil.install(cmakeBuildDir, prefix=distDir, config=buildType, env=env)

        print()  # Add an empty line for cleaner output


setup(
    name="python_cpp_boilerplate",
    version="0.5",
    author="Takeshi Ikuma",
    author_email="tikuma@gmail.com",
    description="Boilerplate for Pybind11 test project",
    long_description="Based on Benjamin Jack's A hybrid Python/C++ test project (https://github.com/benjaminjack/python_cpp_example)",
    packages=find_packages(distDir),
    package_dir={"": distDir},
    ext_modules=[CMakeExtension("python_cpp_boilerplate/example_module")],
    cmdclass=dict(build_ext=CMakeBuild),
    test_suite="tests",
    zip_safe=False,
)
