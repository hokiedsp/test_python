import sys
import multiprocessing
import re
from os import environ, path, name, chdir, makedirs, getcwd, walk, remove
from shutil import which, rmtree
from subprocess import run
from distutils.version import LooseVersion

from lib.vswhere import vswhere


def findexe(cmd):
    """Find a CMake executable """
    if which(cmd) is None and name == "nt":
        cmd += ".exe"
        candidates = [
            path.join(environ[var], "CMake", "bin", cmd)
            for var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "APPDATA", "LOCALAPPDATA")
        ]
        cmd = next(path for path in candidates if which(path))
    return cmd


def validate(cmakePath):
    """Raises FileNotFoundError if cmakePath does not specify a valid cmake executable"""
    min_version = "3.5.0"
    out = run([cmakePath, "--version"], capture_output=True, text=True)
    if not out.check_returncode():
        FileNotFoundError(
            f"CMake file ({cmakePath}) failed to execute with --version argument."
        )
    match = re.match(r"cmake version ([\d.]+)", out.stdout)
    if not match:
        FileNotFoundError(
            f"CMake file ({cmakePath}) failed to provide valid version information."
        )
    cmake_version = LooseVersion(match.group(1))
    if cmake_version < min_version:
        raise FileNotFoundError(f"CMake >= {min_version} is required")


def configured(buildDir):
    """True if CMake project has been configured"""
    return path.isfile(path.join(getcwd(), buildDir, "CMakeCache.txt"))


def clear(buildDir):
    """Clear CMake build directory"""
    for root, dirs, files in walk(buildDir):
        for name in files:
            remove(path.join(root, name))
        for name in dirs:
            rmtree(path.join(root, name))


def configure(**kwargs):
    """run cmake to generate a project buildsystem

    Keyword Args:
    ----------
       S str: Path to root directory of the CMake project to build.
       B str: Path to directory which CMake will use as the root of build directory.
       C str: Pre-load a script to populate the cache.
       D seq(dict): Create or update a CMake CACHE entry from given sequence of
                    dictionaries each with 'var' and 'value' fields with optional 'type' 
                    field
       U str: Remove matching entries from CMake CACHE.
       G str: Specify a build system generator.
       T str: Toolset specification for the generator, if supported.
       A str: Specify platform name if supported by generator
       flags seq(str): Sequence of flags (or any other unlisted argument). Include preceding dash(es).
       env: A mapping that defines the environment variables for the new process
    """

    # prune empty entries
    kwargs = {key: value for key, value in kwargs.items() if value}

    # build cmake arguments
    args = [findexe("cmake")]
    env = None
    for key, value in kwargs.items():
        if key in "SB":
            if not path.isabs(value):
                value = path.normpath(path.join(getcwd(), value))
            kwargs[key] = value
            args.append(f"-{key}")
            args.append(value)
        elif key in "GCUTA":
            args.append(f"-{key}")
            args.append(value)
        elif key == "D":
            for d in value:
                if "type" in d:
                    args.append(f'-D{d["var"]}:{d["type"]}={d["value"]}')
                else:
                    args.append(f'-D{d["var"]}={d["value"]}')
        elif key == "flags":
            for f in value:
                args.append(f)
        elif key == "env":
            env = value
        else:
            raise KeyError(f'Unknown key ("{key}")')

    if "G" in kwargs and kwargs["G"].startswith("Ninja") and name == "nt":
        # to run Ninja in Windows, cmake must first setup vsvc
        vsPath = _getvspath()
        if not vsPath:
            raise FileNotFoundError("Cannot use Ninja because MSVC is not found.")
        args = [_createNinjaBatch(kwargs["B"], vsPath, args, env)]

    run(args, env=env, check=True).check_returncode()


def build(dir, **kwargs):
    """run cmake to generate a project buildsystem

    Parameters:
    ----------
    dir str: Location of the CMake build directory

    Keyword Args:
    ----------
       parallel int: The maximum number of concurrent processes to use when building. Default: 1 less than 
                     the number of available logical cores.
       target str: Path to directory which CMake will use as the root of build directory.
       config  str: For multi-configuration tools, choose specified configuration
       flags seq(str): Sequence of flags (or any other unlisted argument). Include preceding dash(es).
       tooloptions seq(str): Sequence of options to be passed onto the build tool
       env: A mapping that defines the environment variables for the new process
    """

    # prune empty entries
    kwargs = {key: value for key, value in kwargs.items() if value}

    # add defaults if not specified
    if not "parallel" in kwargs:
        kwargs["parallel"] = _getWorkerCount()

    # build cmake arguments
    args = [findexe("cmake"), "--build", dir]
    env = None
    for key, value in kwargs.items():
        if key in ("parallel", "target", "config"):
            args.append(f"--{key}")
            args.append(f"{value}")
        elif key == "flags":
            for f in value:
                args.append(f)
        elif key == "env":
            env = value
        elif key is not "tooloptions":
            raise KeyError

    if "tooloptions" in kwargs:
        args.append("--")
        for f in value:
            args.append(f)

    return run(args, env=env).check_returncode()


def install(dir, **kwargs):
    """run cmake to install an already-generated project binary tree

    Parameters:
    ----------
    dir str: Location of the CMake build directory

    Keyword Args:
    ----------
       prefix str: Override the installation prefix, CMAKE_INSTALL_PREFIX.
       config str: For multi-configuration tools, choose specified configuration
       flags seq(str): Sequence of flags (or any other unlisted argument). Include preceding dash(es).
       env: A mapping that defines the environment variables for the new process
    """

    # prune empty entries
    kwargs = {key: value for key, value in kwargs.items() if value}

    # build cmake arguments
    args = [findexe("cmake"), "--install", dir]
    env = None
    for key, value in kwargs.items():
        if key is "prefix":
            if not path.isabs(value):
                value = path.normpath(path.join(getcwd(), value))
            args.append(f"--{key}")
            args.append(value)
        elif key is "config":
            args.append(f"--{key}")
            args.append(value)
        elif key == "flags":
            for f in value:
                args.append(f)
        elif key == "env":
            env = value
        else:
            raise KeyError

    # return run(' '.join(args), env=env).check_returncode()
    return run(args, env=env).check_returncode()


def ctest(dir, **kwargs):
    """run cmake to generate a project buildsystem

    Parameters:
    ----------
    dir str: Location of the CMake build directory

    Keyword Args:
    ----------
       parallel int: The maximum number of concurrent processes to use when building. Default: 1 less than 
                     the number of available logical cores.
       build-config str: Choose configuration to test.
       options seq(str): Sequence of generic arguments. Include preceding dash(es).
       env: A mapping that defines the environment variables for the new process
    """

    # prune empty entries
    kwargs = {key: value for key, value in kwargs.items() if value}

    # add defaults if not specified
    if not "parallel" in kwargs:
        kwargs["parallel"] = _getWorkerCount()

    args = [findexe("ctest")]
    env = None
    for key, value in kwargs.items():
        if key in ("parallel", "build-config"):
            args.append(f"--{key}")
            args.append(f"{value}")
        elif key == "options":
            for f in value:
                args.append(f)
        elif key == "env":
            env = value
        else:
            raise KeyError

    return run(args, cwd=dir, env=env).check_returncode()


def _getvspath():
    """Use vswhere to obtain VisualStudio path (Windows only)"""
    return vswhere.find_first(latest=True, products=["*"], prop="installationPath")


def _createNinjaBatch(buildDir, vsPath, cmakeArgs, env):
    """Create Windows batch file for Ninja"""
    if not path.exists(buildDir):
        makedirs(buildDir)
    batpath = path.join(buildDir, "cmake_config.bat")

    is_64bits = sys.maxsize > 2 ** 32
    vsdevcmd_args = [
        f'"{path.join(vsPath,"Common7","Tools","VsDevCmd.bat")}"',
        f"-arch={'amd64' if is_64bits else 'x86'}",
        f"-host_arch={'amd64' if is_64bits else 'x86'}",
    ]

    # put arguments with spaces in double quotes
    cmakeArgs = [(f'"{arg}"' if re.search(r"\s", arg) else arg) for arg in cmakeArgs]

    batfile = open(batpath, "w")
    batfile.write(f'CALL {" ".join(vsdevcmd_args)}\n')
    batfile.write(f'CALL {" ".join(cmakeArgs)}\n')
    batfile.close()
    return batpath


def _getWorkerCount():
    return max(multiprocessing.cpu_count() - 1, 1)
