from rare._version import __version__, __version_tuple__

__codename__ = "Boga Discus"

# For PyCharm profiler
if __name__ == "__main__":
    import sys
    from rare.main import main

    sys.exit(main())

__all__ = ["__version__", "__version_tuple__", "__codename__"]
