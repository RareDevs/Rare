import os
from argparse import ArgumentParser

from rare import __version__
from rare.utils import singleton


def main():
    parser = ArgumentParser()
    parser.add_argument("-V", "--version", action="store_true")
    parser.add_argument("-S", "--silent", action="store_true")
    parser.add_argument("--offline", action="store_true")
    subparsers = parser.add_subparsers(title="Commands", dest="subparser")

    launch_parser = subparsers.add_parser("launch")
    launch_parser.add_argument('app_name', help='Name of the app', metavar='<App Name>')

    args = parser.parse_args()

    if args.version:
        print(__version__)
        exit(0)
    try:
        # this object only allows one instance pre machine
        me = singleton.SingleInstance()
    except singleton.SingleInstanceException:
        print("Rare is already running")

        with open(os.path.expanduser("~/.cache/rare/lockfile"), "w") as file:
            if args.subparser == "launch":
                file.write("launch " + args.app_name)
            else:
                file.write("start")
            file.close()

        exit(0)

    if args.subparser == "launch":
        args.silent = True

    from rare.app import start
    start(args)


if __name__ == '__main__':
    main()
