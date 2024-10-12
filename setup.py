import setuptools

from rare import __version__ as version


def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = parse_requirements("requirements.txt")

optional_reqs = dict(
    webview=parse_requirements("requirements-webview.txt"),
    pypresence=parse_requirements("requirements-presence.txt"),
)

setuptools.setup(
    name="Rare",
    version=version,
    author="RareDevs",
    license="GPL-3",
    description="A gui for legendary",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Dummerle/Rare",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        "Operating System :: OS Independent"
    ],
    include_package_data=True,
    python_requires=">=3.9",
    entry_points={
        # 'console_scripts': ["rare = rare.main:main"],
        'gui_scripts': ["rare = rare.main:main"],
    },
    install_requires=requirements,
    extras_require=optional_reqs,
)
