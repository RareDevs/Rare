__version__ = "1.10.4"
__codename__ = "Garlic Crab"

# For PyCharm profiler
if __name__ == "__main__":
    import sys
    from argparse import Namespace
    from rare import client
    status = client.start(Namespace(debug=True, silent=False, offline=False, test_start=False))
    sys.exit(status)
