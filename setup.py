from setuptools import setup, find_packages

setup(
    name='gtexfix',
    version="0.1",
    py_modules = ['to', 'from_'],
    entry_points={
        'console_scripts': [
            'gtexfixto = to:main',
            'gtexfixfrom = from_:main',
        ]
    },
    description='gtexfix',
    install_requires=[],
)
