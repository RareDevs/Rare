import os

import setuptools

from rare import __version__ as version

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = [
    "requests<3.0",
    "pillow",
    "setuptools",
    "wheel",
    "PyQt5",
    "QtAwesome",
    "psutil",
    "pypresence",
    'pywin32; platform_system == "Windows"'
]

if os.name == "nt":
    requirements.append("pywin32")

setuptools.setup(
    name="Rare",
    version=version,
    author="Dummerle",
    license="GPL-3",
    description="A gui for Legendary",
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    url="https://github.com/Dummerle/Rare",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        "Operating System :: OS Independent"
    ],
    python_requires=">=3.8",
    entry_points=dict(console_scripts=["rare=rare.__main__:main"]),
    install_requires=requirements,
)
