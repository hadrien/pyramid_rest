#!/usr/bin/env python
from __future__ import absolute_import
import setuptools

if not getattr(setuptools, "_distribute", False):
    raise SystemExit("""Setuptools is not supported. Please use Distribute""")

setup_requires = [
    'coverage',
    'd2to1',
    'mock',
    'mongokit',
    'nose',
    'nosexcover',
    'webtest',
    'waitress',
    'yanc',
    ]

extras_require = {'mongo': ['mongokit', ]}

setuptools.setup(
    setup_requires=setup_requires,
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
