from datetime import datetime
from logging import getLogger
from pathlib import Path

import requests
from orjson import orjson

from rare.utils import config_helper as config
from rare.utils.paths import data_dir, runtime_assets_path

logger = getLogger('WrapperExe')


def version_tuple(version: str) -> tuple:
    return tuple(version.lstrip('v').split('.'))


_github_api_url = 'https://api.github.com/repos/Etaash-mathamsetty/heroic-epic-integration/releases/latest'


def wrapper_path() -> Path:
    return data_dir().joinpath('EpicGamesLauncher.exe')


def download_lgd_wrapper() -> bool:
    runtime_assets = {
        wrapper_path().name: {
            'version': 'v0.0',
            'date': datetime.isoformat(datetime.min),
        }
    }
    version = runtime_assets[wrapper_path().name]['version']

    if runtime_assets_path().exists():
        runtime_assets = orjson.loads(runtime_assets_path().open('r').read())
        version = runtime_assets.get(wrapper_path().name, {}).get('version', 'v0.0')

    try:
        resp = requests.get(_github_api_url, timeout=5)
        data = resp.content.decode('utf-8')
        latest_release = orjson.loads(data)
    except requests.exceptions.Timeout:
        return wrapper_path().exists()

    remote_assets = latest_release['assets']
    remote_version = latest_release['tag_name']

    if version_tuple(version) >= version_tuple(remote_version) and wrapper_path().exists():
        logger.info('Legendary wrapper already up to date (%s)', version)
        logger.debug('Path: %s', str(wrapper_path()))
        return True

    download_url = remote_assets[0]['browser_download_url']
    logger.info('Updating Legendary wrapper (%s)', remote_version)
    try:
        resp = requests.get(download_url, timeout=5)
        wrapper_path().write_bytes(resp.content)
        config.set_envvar('default', 'LEGENDARY_WRAPPER_EXE', str(wrapper_path))
    except requests.exceptions.Timeout:
        return False

    runtime_assets[wrapper_path().name] = {
        'version': remote_version,
        'date': datetime.isoformat(datetime.fromisoformat(remote_assets[0]['created_at'].replace('Z', '+00:00'))),
    }

    runtime_assets_path().write_text(orjson.dumps(runtime_assets).decode('utf-8'), encoding='utf-8')
    return True


if __name__ == '__main__':
    download_lgd_wrapper()


__all__ = ['download_lgd_wrapper', 'wrapper_path']
