"""The AKABAT package setup script."""

from setuptools import setup, find_packages


def parse_requirements(filename: str) -> list[str]:
    """
    Load requirements.txt and export a list with each requirement.

    Args:
        filename (str): Path to requirements.txt file.

    Returns:
        list[str]: A list with each requirement as an item.
    """
    with open(filename, encoding="utf-8") as f:
        lineiter = [line.strip() for line in f]
    return [line for line in lineiter if line and not line.startswith("#")]


with open("README.rst", encoding="utf-8") as readme_file:
    readme = readme_file.read()

with open("docs/history.rst", encoding="utf-8") as history_file:
    history = history_file.read()

requirements = parse_requirements("requirements.txt")

setup_requirements = [
    # setup requirements (distutils extensions, etc.) here
]

# test_requirements = parse_requirements("requirements_dev.txt")

setup(
    name="akabat",
    version="0.1.1",
    description="Advanced Knowledge Aggregator for Bibliometric Analysis and Trends",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/x-rst",
    author="Francisco Enguix",
    author_email="enguixfco@gmail.com",
    url="https://github.com/FranEnguix/akabat",
    packages=find_packages(include=["akabat", "akabat.*"]),
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords="akabat",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
)
