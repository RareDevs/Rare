from setuptools import setup

from setuptools_scm import ScmVersion


def mkversion(ver: ScmVersion) -> str:
    return f"{ver.tag}.{ver.distance}"


setup(use_scm_version={"version_scheme": mkversion})
