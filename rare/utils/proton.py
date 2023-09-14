import os
from logging import getLogger

logger = getLogger("Proton")


def find_proton_combos():
    possible_proton_combos = []
    compatibilitytools_dirs = [
        os.path.expanduser("~/.steam/steam/steamapps/common"),
        "/usr/share/steam/compatibilitytools.d",
        os.path.expanduser("~/.steam/compatibilitytools.d"),
        os.path.expanduser("~/.steam/root/compatibilitytools.d"),
    ]
    for c in compatibilitytools_dirs:
        if os.path.exists(c):
            for i in os.listdir(c):
                proton = os.path.join(c, i, "proton")
                compatibilitytool = os.path.join(c, i, "compatibilitytool.vdf")
                toolmanifest = os.path.join(c, i, "toolmanifest.vdf")
                if os.path.exists(proton) and (
                        os.path.exists(compatibilitytool) or os.path.exists(toolmanifest)
                ):
                    wrapper = f'"{proton}" run'
                    possible_proton_combos.append(wrapper)
    if not possible_proton_combos:
        logger.warning("Unable to find any Proton version")
    return possible_proton_combos
