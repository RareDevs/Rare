#!/usr/bin/python

import os
import pathlib
import sys
from argparse import ArgumentParser


def main():

    # fix cx_freeze
    import multiprocessing
    multiprocessing.freeze_support()

    # insert legendary for installed via pip/setup.py submodule to path
    if not __name__ == "__main__":
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "legendary"))

    # CLI Options
    parser = ArgumentParser()
    parser.add_argument("-V", "--version", action="store_true", help="Shows version and exits")
    parser.add_argument("-S", "--silent", action="store_true",
                        help="Launch Rare in background. Open it from System Tray Icon")
    parser.add_argument("--debug", action="store_true", help="Launch in debug mode")
    parser.add_argument("--offline", action="store_true", help="Launch Rare in offline mode")
    parser.add_argument("--test-start", action="store_true", help="Quit immediately after launch")

    parser.add_argument("--desktop-shortcut", action="store_true", dest="desktop_shortcut",
                        help="Use this, if there is no link on desktop to start Rare")
    parser.add_argument("--startmenu-shortcut", action="store_true", dest="startmenu_shortcut",
                        help="Use this, if there is no link in start menu to launch Rare")
    subparsers = parser.add_subparsers(title="Commands", dest="subparser")

    launch_parser = subparsers.add_parser("launch")
    launch_parser.add_argument('app_name', help='Name of the app', metavar='<App Name>')

    args = parser.parse_args()

    if args.desktop_shortcut:
        from rare.utils import utils
        utils.create_rare_desktop_link("desktop")
        print("Link created")

    if args.startmenu_shortcut:
        from rare.utils import utils
        utils.create_rare_desktop_link("start_menu")
        print("link created")

    if args.version:
        from rare import __version__, code_name
        print(f"Rare {__version__} Codename: {code_name}")
        return
    from rare.utils import singleton
    try:
        # this object only allows one instance per machine

        me = singleton.SingleInstance()
    except singleton.SingleInstanceException:
        print("Rare is already running")
        from rare import data_dir
        with open(os.path.join(data_dir, "lockfile"), "w") as file:
            if args.subparser == "launch":
                file.write("launch " + args.app_name)
            else:
                file.write("start")
            file.close()
        return

    if args.subparser == "launch":
        args.silent = True

    from rare.app import start
    start(args)


if __name__ == '__main__':
    # run from source
    # insert raw legendary submodule
    sys.path.insert(0, os.path.join(pathlib.Path(__file__).parent.absolute(), "legendary"))
    # insert source directory
    sys.path.insert(0, str(pathlib.Path(__file__).parents[1].absolute()))

    main()
