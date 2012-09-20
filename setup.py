#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

setup_requires = [
    'd2to1',
    'nose',
    'nosexcover',
    'coverage',
    'mock',
    'webtest',
]

setup(
    setup_requires=setup_requires,
    d2to1=True,
    package_data={
    },
    entry_points="""
    [paste.app_factory]
        main = pyramid_rest:main
    """,
    paster_plugins=['pyramid'],
)
