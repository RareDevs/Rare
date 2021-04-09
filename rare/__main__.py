from argparse import ArgumentParser
from rare import __version__
from rare.utils import singleton


def main():
    parser = ArgumentParser()
    parser.add_argument("-V", "--version", action="store_true")
    parser.add_argument("-S", "--silent", action="store_true")

    args = parser.parse_args()
    if args.version:
        print(__version__)
        exit(0)
    try:
        # this object only allows one instance pre machine
        me = singleton.SingleInstance()
    except singleton.SingleInstanceException:
        print("Rare is already running")
        exit(0)

    from rare.app import start
    start(args)


if __name__ == '__main__':
    main()
