import os
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import requests

INNOSETUP_VERSION = '7.0.2'
USER_AGENT = 'Rare-IS-Builder / 1.0 https://github.com/RareDevs/Rare'

GITHUB_HEADERS = {'Accept': 'application/vnd.github+json', 'User-Agent': USER_AGENT, 'X-GitHub-Api-Version': '2026-03-10'}
MY_DIR = Path(__file__).parent
REPO_ROOT = MY_DIR.parent.parent

PACKAGE_ARCH = os.environ.get('INNOSETUP_PACKAGE_ARCH', 'x86_64')
PACKAGE_FILES = os.environ.get('INNOSETUP_PACKAGE_FILES')
try:
    from rare import __version__
    PACKAGE_VERSION = __version__
except ImportError:
    __version__ = '0.0.0.0'
    PACKAGE_VERSION = os.environ.get('INNOSETUP_PACKAGE_VERSION', __version__)


def install_innosetup() -> None:
    if find_iscc() is not None:
        return

    tag = f'is-{INNOSETUP_VERSION.replace(".", "_")}'

    release_response = requests.get(f'https://api.github.com/repos/jrsoftware/issrc/releases/tags/{tag}', headers=GITHUB_HEADERS)
    release_response.raise_for_status()
    release_response_parsed: dict[str, Any] = release_response.json()

    release_assets = release_response_parsed.get('assets', [])
    x64_installer = next(asset for asset in release_assets if asset.get('name').endswith('-x64.exe'))

    setup_response = requests.get(x64_installer.get('browser_download_url'), headers=GITHUB_HEADERS)
    setup_response.raise_for_status()
    with NamedTemporaryFile(delete_on_close=False, suffix='.exe') as tf:
        tf.write(setup_response.content)
        tf.close()
        subprocess.run(
            [
                tf.name,
                '/VERYSILENT',
                '/SUPPRESSMSGBOXES',
                '/NORESTART',
                '/SP-',
            ],
            check=True,
        )


def find_iscc() -> Path | None:
    iscc_path = Path(os.getenv('ProgramFiles', '')) / 'Inno Setup 7' / 'ISCC.exe'  # noqa: SIM112
    if iscc_path.exists():
        return iscc_path
    return None


def try_make_numeric(version_str: str) -> str:
    def make_component_numeric(component: str) -> str | None:
        if component.isnumeric():
            return component

        if (without_dev := component.replace('dev', '')).isnumeric():
            return without_dev

        return None

    return '.'.join(filter(bool, map(make_component_numeric, version_str.split('.'))))


def main():
    if sys.platform != 'win32':
        print('This script can only run on Windows')
        sys.exit(1)

    iscc_path = find_iscc()
    if iscc_path is None:
        install_innosetup()
        iscc_path = find_iscc()
        if iscc_path is None:
            raise RuntimeError('Did not find "iscc" executable after installation')

    if PACKAGE_FILES is None:
        installer_files = list((REPO_ROOT / 'build').glob('exe.win*'))
        if not installer_files:
            raise RuntimeError(f'Did not find an "exe.win..." folder in {REPO_ROOT / "build"}. Did you run "freeze.py build_exe"?')
        if len(installer_files) > 1:
            print(f'Warning: Found multiple executable directories in {REPO_ROOT / "build"}. Choosing {installer_files[0]}')
        files_dir = installer_files[0]
    else:
        files_dir = REPO_ROOT / PACKAGE_FILES
        if not files_dir.is_dir():
            raise RuntimeError(f'Did not find folder {files_dir}. Did you build the project first?')

    if PACKAGE_ARCH == 'arm64':
        app_architecture = app_platform = 'arm64'
    else:
        app_architecture = 'x64compatible'
        app_platform = 'x86_64'

    subprocess.run(
        [
            iscc_path,
            f'/dAppVersion={try_make_numeric(PACKAGE_VERSION)}',
            f'/dNumericVersion={try_make_numeric(PACKAGE_VERSION)}',
            f'/dAppArchitecture={app_architecture}',
            f'/dAppPlatform={app_platform}',
            f'/dSourceDir={REPO_ROOT}',
            f'/dFilesDir={files_dir}',
            MY_DIR / 'setup.iss',
        ],
        check=True,
    )


if __name__ == '__main__':
    main()
