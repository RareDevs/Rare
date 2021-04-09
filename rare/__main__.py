from argparse import ArgumentParser
from rare import __version__

def main():
    parser = ArgumentParser()
    parser.add_argument("-V", "--version", action="store_true")
    parser.add_argument("-S", "--silent", action="store_true")

    args = parser.parse_args()
    if args.version:
        print(__version__)
        exit(0)

    from rare.app import start
    start(args)


if __name__ == '__main__':
    main()
