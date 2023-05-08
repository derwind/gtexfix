from setuptools import setup

setup(
    name='gtexfix',
    version='0.1',
    description='gtexfix',
    packages=['gtexfix'],
    entry_points={
        'console_scripts': [
            'gtexfixto = gtexfix.to:main',
            'gtexfixfrom = gtexfix.from_:main',
        ]
    },
    install_requires=[],
)
