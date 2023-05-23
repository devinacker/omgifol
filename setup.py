#!/usr/bin/env python

from setuptools import setup, find_packages
import glob

setup(
	name = 'omgifol',
	version = '0.5.1',
	description = 'A Python library for manipulation of Doom WAD files',
	url = 'https://github.com/devinacker/omgifol',
	author = 'Devin Acker, Fredrik Johansson',
	author_email = 'd@revenant1.net',
	license = 'MIT',
	classifiers = [
		'Development Status :: 3 - Alpha',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3',
		'Operating System :: OS Independent',
	],
	python_requires = ">=3.3",
	packages = find_packages(exclude = ['demo']),
	scripts = glob.glob("demo/*.py"),
)
