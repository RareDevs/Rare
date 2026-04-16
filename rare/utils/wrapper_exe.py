from datetime import datetime
from typing import Tuple

import requests
from orjson import orjson

from rare.utils import config_helper as config
from rare.utils.paths import data_dir, runtime_assets_json


def version_tuple(version: str) -> Tuple:
    return tuple(version.lstrip('v').split('.'))


_github_api_url = 'https://api.github.com/repos/Etaash-mathamsetty/heroic-epic-integration/releases/latest'


def download_wrapper_exe():
    wrapper_exe = data_dir().joinpath('EpicGamesLauncher.exe')

    if not wrapper_exe.exists():
        config.remove_envvar('default', 'LEGENDARY_WRAPPER_EXE')

    runtime_assets = {
        wrapper_exe.name: {
            'version': 'v0.0',
            'date': datetime.isoformat(datetime.min),
        }
    }
    version = runtime_assets[wrapper_exe.name]['version']

    if runtime_assets_json().exists():
        runtime_assets = orjson.loads(runtime_assets_json().open('r').read())
        version = runtime_assets.get(wrapper_exe.name, {}).get('version', 'v0.0')

    try:
        resp = requests.get(_github_api_url, timeout=5)
        data = resp.content.decode('utf-8')
        latest_release = orjson.loads(data)
    except requests.exceptions.Timeout:
        return

    remote_assets = latest_release['assets']
    remote_version = latest_release['tag_name']

    if version_tuple(version) >= version_tuple(remote_version):
        if wrapper_exe.exists() and config.get_envvar('default', 'LEGENDARY_WRAPPER_EXE', '') == str(wrapper_exe):
            return

        if wrapper_exe.exists():
            config.set_envvar('default', 'LEGENDARY_WRAPPER_EXE', str(wrapper_exe))
            return

    download_url = remote_assets[0]['browser_download_url']
    try:
        resp = requests.get(download_url, timeout=5)
        wrapper_exe.write_bytes(resp.content)
        config.set_envvar('default', 'LEGENDARY_WRAPPER_EXE', str(wrapper_exe))
    except requests.exceptions.Timeout:
        return

    runtime_assets[wrapper_exe.name] = {
        'version': remote_version,
        'date': datetime.isoformat(datetime.fromisoformat(remote_assets[0]['created_at'].replace('Z', '+00:00'))),
    }

    runtime_assets_json().write_text(orjson.dumps(runtime_assets).decode('utf-8'), encoding='utf-8')
    return


if __name__ == '__main__':
    download_wrapper_exe()


__all__ = ['download_wrapper_exe']
