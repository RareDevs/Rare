import os
import pathlib
import sys

if __name__ == "__main__":
    from rare.main import main

    # run from source
    # insert raw legendary submodule
    # sys.path.insert(
    #     0, os.path.join(pathlib.Path(__file__).parent.absolute(), "legendary")
    # )

    # insert source directory
    if "__compiled__" not in globals():
        sys.path.insert(0, str(pathlib.Path(__file__).parents[1].absolute()))

    # If we are on Windows, and we are in a "compiled" GUI application form
    # stdout (and stderr?) will be None. So to avoid `'NoneType' object has no attribute 'write'`
    # errors, redirect both of them to devnull
    if os.name == "nt" and (getattr(sys, "frozen", False) or ("__compiled__" in globals())):
        # Check if stdout and stderr are None before redirecting
        # This is useful in the case of test builds that enable console
        if sys.stdout is None:
            sys.stdout = open(os.devnull, 'w')
        if sys.stderr is None:
            sys.stderr = open(os.devnull, 'w')

    sys.exit(main())
