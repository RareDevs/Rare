import random
import sys

from setuptools_scm import ScmVersion, get_version

def mknumeric(ver: ScmVersion) -> str:
    return f"{ver.tag}.{ver.distance}"


def mkname() -> str:
    from legendary.core import LegendaryCore

    core = LegendaryCore()
    core.login()

    return " ".join(
        map(
            lambda game: game.app_name,
            random.choices(list(filter(lambda x: len(x.app_name) != 32, core.get_game_list(False))), k=2),
        )
    )


if __name__ == "__main__":
    version = get_version(
        root='..',
        relative_to=__file__,
        git_describe_command=["git", "describe", "--dirty", "--long"],
        version_scheme=mknumeric,
        local_scheme="no-local-version"
    )
    sys.stdout.write(version)
    sys.stdout.write("\n")
    sys.stdout.write(mkname())
    sys.stdout.write("\n")
    sys.exit(0)
