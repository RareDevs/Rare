import multiprocessing
import os
from argparse import ArgumentParser


def main() -> int:
    # fix cx_freeze
    multiprocessing.freeze_support()

    # insert legendary for installed via pip/setup.py submodule to path
    # if not __name__ == "__main__":
    #     sys.path.insert(0, os.path.join(os.path.dirname(__file__), "legendary"))

    # CLI Options
    parser = ArgumentParser()
    parser.add_argument(
        "-V", "--version", action="store_true", help="Shows version and exits"
    )
    parser.add_argument(
        "-S",
        "--silent",
        action="store_true",
        help="Launch Rare in background. Open it from System Tray Icon",
    )
    parser.add_argument("--debug", action="store_true", help="Launch in debug mode")
    parser.add_argument(
        "--offline", action="store_true", help="Launch Rare in offline mode"
    )
    parser.add_argument(
        "--test-start", action="store_true", help="Quit immediately after launch"
    )

    parser.add_argument(
        "--desktop-shortcut",
        action="store_true",
        dest="desktop_shortcut",
        help="Use this, if there is no link on desktop to start Rare",
    )
    parser.add_argument(
        "--startmenu-shortcut",
        action="store_true",
        dest="startmenu_shortcut",
        help="Use this, if there is no link in start menu to launch Rare",
    )
    subparsers = parser.add_subparsers(title="Commands", dest="subparser")

    launch_minimal_parser = subparsers.add_parser("start", aliases=["launch"])
    launch_minimal_parser.add_argument("app_name", help="AppName of the game to launch",
                                       metavar="<App Name>", action="store")
    launch_minimal_parser.add_argument("--dry-run", help="Print arguments and exit", action="store_true")
    launch_minimal_parser.add_argument("--offline", help="Launch game offline",
                                       action="store_true")
    launch_minimal_parser.add_argument('--wine-bin', dest='wine_bin', action='store', metavar='<wine binary>',
                                       default=os.environ.get('LGDRY_WINE_BINARY', None),
                                       help='Set WINE binary to use to launch the app')
    launch_minimal_parser.add_argument('--wine-prefix', dest='wine_pfx', action='store', metavar='<wine pfx path>',
                                       default=os.environ.get('LGDRY_WINE_PREFIX', None),
                                       help='Set WINE prefix to use')
    launch_minimal_parser.add_argument("--ask-sync-saves", help="Ask to sync cloud saves",
                                       action="store_true")
    launch_minimal_parser.add_argument("--skip-update-check", help="Do not check for updates",
                                       action="store_true")

    args = parser.parse_args()

    if args.desktop_shortcut or args.startmenu_shortcut:
        from rare.utils.paths import create_desktop_link

        if args.desktop_shortcut:
            create_desktop_link(app_name="rare_shortcut", link_type="desktop")

        if args.startmenu_shortcut:
            create_desktop_link(app_name="rare_shortcut", link_type="start_menu")

        print("Link created")
        return 0

    if args.version:
        from rare import __version__, __codename__
        print(f"Rare {__version__} Codename: {__codename__}")
        return 0

    if args.subparser == "start" or args.subparser == "launch":
        from rare.launcher import launch
        return launch(args)

    from rare.utils import singleton

    try:
        # this object only allows one instance per machine

        me = singleton.SingleInstance()
    except singleton.SingleInstanceException:
        print("Rare is already running")
        from rare.utils.paths import lock_file

        with open(lock_file(), "w") as file:
            file.write("show")
            file.close()
        return -1

    from rare.components import start
    return start(args)
