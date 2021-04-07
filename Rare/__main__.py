import sys


def main():
    if "--version" in sys.argv:
        from Rare import __version__

        print(__version__)
        exit(0)

    from Rare.Main import start
    start()


if __name__ == '__main__':
    main()
