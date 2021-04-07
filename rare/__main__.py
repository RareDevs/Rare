import sys


def main():
    if "--version" in sys.argv:
        from rare import __version__

        print(__version__)
        exit(0)

    from rare.App import start
    start()


if __name__ == '__main__':
    main()
