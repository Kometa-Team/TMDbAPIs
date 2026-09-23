import os

from setuptools import setup, find_packages

PACKAGE_NAME = "tmdbapis"
DESCRIPTION = "A lightweight Python library for The V3 TMDb APIs."
URL = "https://github.com/Kometa-Team/TMDbAPIs"
AUTHOR = "meisnate12"
AUTHOR_EMAIL = "kometateam@proton.me"
LICENSE = "MIT License"

with open("README.rst", "r") as f:
    long_descr = f.read()

__version__ = None
if os.path.exists("VERSION"):
    with open("VERSION") as handle:
        for line in handle.readlines():
            line = line.strip()
            if len(line) > 0:
                __version__ = line
                break

setup(
    name=PACKAGE_NAME,
    version=__version__,
    description=DESCRIPTION,
    long_description=long_descr,
    url=URL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    packages=find_packages(),
    python_requires=">=3.8",
    keywords=["tmdbapis", "tmdbapi", "tmdb", "wrapper", "api"],
    install_requires=[
      "requests",
      "setuptools"
    ],
    project_urls={
      "Documentation": "https://tmdbapis.kometa.wiki",
      "Funding": "https://github.com/sponsors/meisnate12",
      "Source": "https://github.com/Kometa-Team/TMDbAPIs",
      "Issues": "https://github.com/Kometa-Team/TMDbAPIs/issues",
    },
    classifiers=[
      "Development Status :: 5 - Production/Stable",
      "Intended Audience :: Developers",
      "Topic :: Software Development :: Libraries",
      "Programming Language :: Python",
      "Programming Language :: Python :: 3.8",
      "Programming Language :: Python :: 3.9",
      "Programming Language :: Python :: 3.10",
      "Programming Language :: Python :: 3.11",
      "Programming Language :: Python :: 3.12",
    ]
)

