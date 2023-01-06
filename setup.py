import setuptools

from rare import __version__ as version

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = [
    "requests<3.0",
    "legendary-gl==0.20.32",
    "setuptools",
    "wheel",
    "PyQt5",
    "QtAwesome",
    'pywin32; platform_system == "Windows"',
    "typing_extensions"
]

optional_reqs = dict(
    webview=[
        'pywebview[gtk]; platform_system == "Linux"',
        'pywebview[cef]; platform_system == "Windows"',
    ],
    pypresence=["pypresence"]
)

setuptools.setup(
    name="Rare",
    version=version,
    author="Dummerle",
    license="GPL-3",
    description="A gui for Legendary",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Dummerle/Rare",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        "Operating System :: OS Independent"
    ],
    include_package_data=True,
    python_requires=">=3.9",
    entry_points=dict(console_scripts=["rare=rare.__main__:main"]),
    install_requires=requirements,
    extras_require=optional_reqs,
)
