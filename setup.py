#!/usr/bin/env python
import setuptools

if not getattr(setuptools, "_distribute", False):
    raise SystemExit("""Setuptools is not supported. Please use Distribute""")

setup_requires = [
    'd2to1',
    ]

tests_require = [
    'coverage',
    'mock',
    'mongokit',
    'nose',
    'nosexcover',
    'webtest',
    'waitress',
    'yanc',
    ]

extras_require = {'mongo': ['pyramid_mongokit']}

setuptools.setup(
    setup_requires=setup_requires,
    tests_require=tests_require,
    extras_require=extras_require,
    d2to1=True,
    package_data={
        },
    entry_points="""
        [paste.app_factory]
            main = pyramid_rest:main
        """,
    paster_plugins=['pyramid'],
    )
