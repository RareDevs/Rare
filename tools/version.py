from setuptools_scm import ScmVersion, get_version

version = get_version(root="..", relative_to=__file__)


def make(ver: ScmVersion) -> str:
    return f"{ver.tag}.{ver.distance}"
