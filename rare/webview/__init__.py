import sys
from argparse import Namespace

from legendary.utils import webview_login


def launch(args: Namespace) -> int:
    if webview_login.do_webview_login(
            callback_code=sys.stdout.write, user_agent=f'EpicGamesLauncher/{args.egl_version}'
    ):
        return 0
    else:
        return 1
