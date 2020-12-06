from distutils.core import Extension
from distutils.errors import CCompilerError, DistutilsExecError, DistutilsPlatformError
from distutils.command.build_ext import build_ext


ext_modules = [
    Extension('test_extension._test_extension',
              sources=['test_extension/test_extension.c'],
              extra_compile_args=['-g']),
]


class BuildFailed(Exception):
    pass


class ExtBuilder(build_ext):

    def run(self):
        try:
            build_ext.run(self)
        except (DistutilsPlatformError, FileNotFoundError):
            print('Could not compile C extension.')

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except (CCompilerError, DistutilsExecError, DistutilsPlatformError, ValueError):
            print('Could not compile C extension.')


def build(setup_kwargs):
    setup_kwargs.update(
        {'ext_modules': ext_modules, 'cmdclass': {'build_ext': ExtBuilder}}
    )
