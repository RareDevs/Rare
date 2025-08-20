import multiprocessing
import os
import pathlib
import platform
import sys
from argparse import ArgumentParser


def main() -> int:
    # If we are on Windows, and we are in a "compiled" GUI application form
    # stdout (and stderr?) will be None. So to avoid `'NoneType' object has no attribute 'write'`
    # errors, redirect both of them to devnull
    if os.name == "nt" and (getattr(sys, "frozen", False) or ("__compiled__" in globals())):
        # Check if stdout and stderr are None before redirecting
        # This is useful in the case of test builds that enable console
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w")

    os.environ["QT_QPA_PLATFORMTHEME"] = ""
    if "LEGENDARY_CONFIG_PATH" in os.environ:
        os.environ["LEGENDARY_CONFIG_PATH"] = os.path.expanduser(os.environ["LEGENDARY_CONFIG_PATH"])

    # fix cx_freeze
    multiprocessing.freeze_support()

    # CLI Options
    parser = ArgumentParser()
    parser.add_argument("-V", "--version", action="store_true", help="Shows version and exits")
    parser.add_argument(
        "-S",
        "--silent",
        action="store_true",
        help="Launch Rare in background. Open it from System Tray Icon",
    )
    parser.add_argument("--debug", action="store_true", help="Launch in debug mode")
    parser.add_argument("--offline", action="store_true", help="Launch Rare in offline mode")
    parser.add_argument("--test-start", action="store_true", help="Quit immediately after launch")

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

    # Launch command
    launch_parser = subparsers.add_parser("launch", aliases=["start"])
    launch_parser.add_argument("--dry-run", action="store_true", help="Print arguments and exit")
    launch_parser.add_argument("--offline", action="store_true", help="Launch game offline")
    launch_parser.add_argument("--ask-sync-saves", action="store_true", help="Ask to sync cloud saves")
    launch_parser.add_argument("--skip-update-check", action="store_true", help="Do not check for updates")
    launch_parser.add_argument(
        "--show-console",
        action="store_true",
        help="Show a console window to log the application's output",
    )
    if platform.system() != "Windows":
        launch_parser.add_argument(
            "--wine-bin",
            action="store",
            dest="wine_bin",
            default=os.environ.get("LGDRY_WINE_BINARY", None),
            metavar="<wine binary>",
            help="Set WINE binary to use to launch the app",
        )
        launch_parser.add_argument(
            "--wine-prefix",
            action="store",
            dest="wine_pfx",
            default=os.environ.get("LGDRY_WINE_PREFIX", None),
            metavar="<wine pfx path>",
            help="Set WINE prefix to use",
        )
    launch_parser.add_argument(
        "app_name",
        action="store",
        metavar="<App Name>",
        help="AppName of the game to launch",
    )

    # Login command
    login_parser = subparsers.add_parser("login", aliases=["auth"])
    login_parser.add_argument(
        "egl_version",
        action="store",
        metavar="<EGL Version>",
        help="Epic Games Launcher User Agent version",
    )

    # Subreaper command
    subreaper_parser = subparsers.add_parser("subreaper", aliases=["reaper"])
    subreaper_parser.add_argument(
        "--workdir",
        action="store",
        dest="workdir",
        metavar="<workdir>",
        help="Run command in this directory",
    )

    subreaper_parser.add_argument(
        "command",
        action="store",
        metavar="<command>",
        help="Command to execute in the subreaper",
    )

    args, other = parser.parse_known_args()

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

    if args.subparser in {"login", "auth"}:
        from rare.commands.webview import webview

        return webview(args)

    if args.subparser in {"launch", "start"}:
        from rare.commands.launcher import launcher

        return launcher(args)

    if args.subparser in {"subreaper", "reaper"}:
        from rare.commands.subreaper import subreaper

        return subreaper(args, other)

    from rare.utils import singleton

    try:
        # this object only allows one instance per machine

        me = singleton.SingleInstance()  # noqa: F841
    except singleton.SingleInstanceException:
        print("Rare is already running")
        from rare.utils.paths import lock_file

        with open(lock_file(), "w") as file:
            file.write("show")
            file.close()
        return -1

    from rare.components import start

    return start(args)


if __name__ == "__main__":
    # insert source directory if running `main.py` as python script
    # Required by AppImage
    if "__compiled__" not in globals():
        sys.path.insert(0, str(pathlib.Path(__file__).parents[1].absolute()))

    sys.exit(main())
