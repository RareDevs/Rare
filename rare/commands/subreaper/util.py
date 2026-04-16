import os
import shutil
from typing import List


def find_all(name, path) -> List:
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result


def find_mangohud_shim() -> str:
    libs = find_all('libMangoHud_shim.so', '/usr')
    if 1 > len(libs) > 2:
        return ''
    if len(libs) == 1:
        return libs[0]
    ret = []
    for left, right in zip(*(lib.split('/') for lib in libs)):
        if left == right:
            ret.append(left)
        elif left.startswith('lib') and right.startswith('lib'):
            ret.append('$LIB')
        else:
            return ''
    return '/'.join(ret)


def find_mangohud_bin() -> str:
    return shutil.which('mangohud')


if __name__ == '__main__':
    print(find_mangohud_shim())


__all__ = ['find_mangohud_shim', 'find_mangohud_bin']
