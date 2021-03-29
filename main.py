import zipfile
import sys
import pathlib
import hashlib
import json
from collections import defaultdict


def remove_top_path(path):
    return "/".join(str(path).split("/")[1:])


def get_hash(path: pathlib.Path, top=True):
    if path.is_file():
        hex_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if top:
            return {remove_top_path(path): hex_digest}
        else:
            return hex_digest
    else:
        hash_dir = {
            remove_top_path(child): get_hash(child, False) for child in path.iterdir()
        }
        return hash_dir


class BaseArchive:
    def __init__(self, path):
        self.root = None

    def get_child_hashes(self):
        hashes = {}
        for child in self.root.iterdir():
            hashes |= get_hash(child)
        return hashes


class Directory(BaseArchive):
    def __init__(self, path):
        self.root = pathlib.Path(path)


class Zip(BaseArchive):
    def __init__(self, path):
        self.zf = zipfile.ZipFile(path)
        self.root = zipfile.Path(self.zf)


def main():
    pathes = sys.argv[1:3]
    if len(pathes) != 2:
        raise ValueError("Only two arguments are allowed.")

    archives: list[BaseArchive] = []

    for path in pathes:
        file = pathlib.Path(path)
        if not file.exists():
            raise FileNotFoundError()

        if file.is_dir():
            archive = Directory(file)
        elif file.is_file() and file.suffix == ".zip":
            archive = Zip(file)
        else:
            raise ValueError()

        archives.append(archive)

    hash_list = list(map(lambda x: x.get_child_hashes(), archives))

    all_file_names = {key for hashes in hash_list for key in hashes.keys()}
    all_file_data = defaultdict(set)
    nofile_names = set()

    for hashes in hash_list:
        nofile_names = nofile_names.union(all_file_names - set(hashes.keys()))

        for file, hash_ in hashes.items():
            all_file_data[file].add(hash_)

    if nofile_names:
        print("[片方にしかないファイル]")
        print("\n".join(sorted(list(nofile_names))))

    different_files = [
        file for file, hashes in all_file_data.items() if len(hashes) != 1
    ]
    if different_files:
        print("[内容の違うファイル]")
        print("\n".join(sorted(different_files)))


if __name__ == "__main__":
    main()
