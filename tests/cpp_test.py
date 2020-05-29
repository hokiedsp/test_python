import unittest
import subprocess
from os import path, getcwd

import cmakeutil


class MainTest(unittest.TestCase):
    def test_cpp(self):
        print("\n\nTesting C++ code...")
        cmakeutil.ctest(path.normpath(path.join(__file__, "../../build")))
        print("\nResuming Python tests...\n")


if __name__ == "__main__":
    unittest.main()
