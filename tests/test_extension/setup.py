from setuptools import Extension, setup

setup(
    ext_modules=[
        Extension('test_extension._test_extension',
                  sources=['test_extension/test_extension.c'],
                  extra_compile_args=[
                    '-g',   # generate debug symbols
                    '-O0',  # disable compiler optimizations
                  ]),
    ]
)
