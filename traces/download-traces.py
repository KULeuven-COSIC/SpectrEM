# Script to download and extract the pre-recorded SpectrEM traces.
#
# This file interfaces with the API provided by KU Leuven RDR to autimatically
# download the pre-recorded traces. As the traces stored in RDR are compressed,
# this script will subsequently extract all downloaded traces.
#
# Last modified: 2023-08-08

import os
import tarfile
import requests

from glob import glob
from os.path import dirname, join, relpath, getsize, normpath
from split_file_reader import SplitFileReader
from tqdm import tqdm


q = "https://rdr.kuleuven.be/api/datasets/:persistentId/?persistentId=doi:10.48804/AHTI1A"
headers = {}

# https://stackoverflow.com/a/3668977
class ProgressFileObject(SplitFileReader):
    def __init__(self, dir, total_size, *args, **kwargs):
        self._pbar = tqdm(total=total_size, desc=f"Extracting {dir}", unit="B", unit_scale=True)
        SplitFileReader.__init__(self, *args, **kwargs)

    def read(self, size):
        self._pbar.update(self.tell() - self._pbar.n)
        return SplitFileReader.read(self, size)
    
    def close(self):
        self._pbar.close()
        SplitFileReader.close(self)

# https://stackoverflow.com/a/16696317
def download_file(url, local_filename, rel_filename, i, tot):
    os.makedirs(dirname(local_filename), exist_ok=True)  # Make sure the directory exists
    with requests.get(url, stream=True, headers=headers) as r:
        r.raise_for_status()
        size = int(r.raw.headers.get('Content-Length'))
        with tqdm(total=size, desc=f"({i+1}/{tot}) {rel_filename}", unit="B", unit_scale=True) as pbar:
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=16384): 
                    f.write(chunk)
                    pbar.update(min(16384, size - pbar.n))

# Access list of files
r = requests.get(q)

files = r.json()["data"]["latestVersion"]["files"]

dirs = dict({x["directoryLabel"].split("/")[0]:0 for x in files if "directoryLabel" in x})


print("This dataset contains the following directories:")
for dir in sorted(dirs):
    dirs[dir] = sum(map(lambda x: x["dataFile"]["filesize"] if "directoryLabel" in x and x["directoryLabel"].startswith(dir) else 0, files))

    print(f"  {dir:25s} {dirs[dir]/1e9:06.3f} GB")


print("\nPlease specify which directories to download:")
files_to_download = dict()
dirs_to_download = set()
files_sizes = dict()
total_size = 0

for dir in sorted(dirs):
    y = input(f"  {dir:25s} ({dirs[dir]/1e9:06.3f} GB) [y/n]: ")

    if y.lower() == "y":
        dirs_to_download.add(dir)

        files_to_download |= {normpath(f"{x['directoryLabel']}/{x['label']}"): x["dataFile"]["id"] for x in files if "directoryLabel" in x and x["directoryLabel"].startswith(dir)}
        files_sizes |= {normpath(f"{x['directoryLabel']}/{x['label']}"): x["dataFile"]["filesize"] for x in files if "directoryLabel" in x and x["directoryLabel"].startswith(dir)}
        total_size += dirs[dir]

print("\nPlease specify Where to download the traces to. Leave emtpy for current working directory.")
traces_dir = input("Download location: ")
if len(traces_dir) == 0:
    traces_dir = os.getcwd()

# Find all files that have already been downloaded to the traces_dir
downloaded_files = {join(relpath(path, traces_dir), filename): getsize(join(path, filename)) for path, _, files in os.walk(traces_dir) for filename in files}
downloaded_files = {key for key in files_sizes if key in downloaded_files and files_sizes[key] == downloaded_files[key]}

# Filter out any files that have already been downloaded
files_to_download = {key: value for key, value in files_to_download.items() if key not in downloaded_files}

print(f"\nTotal download size: {total_size/1e9:.3f} GB")
print(f"Remaining download size: {sum(files_sizes[key] for key in files_sizes if key in files_to_download)/1e3:.9f} GB")
print(f"Free disk space required: {(sum(files_sizes.values()) + total_size*1.85)/1e9:.3f} GB")
print(f"Files will be downloaded and extracted in the following directory: {traces_dir}")
y = input("Proceed [y/n]? ")

if y.lower() != "y":
    exit()

# Downloading files

print(f"\nDownloading {len(files_to_download)} files")
for i, file in enumerate(sorted(files_to_download)):
    filepath = join(traces_dir, file)
    download_file(f"https://rdr.kuleuven.be/api/access/datafile/{files_to_download[file]}", filepath, file, i, len(files_to_download))

# Extracting files

print("\nExtracting the downloaded files")
for i, dir in enumerate(dirs_to_download):
    dirpath = join(traces_dir, dir)
    filepaths = sorted(glob(join(traces_dir, dir, "*.tar.bz2*")))

    total_size = sum(map(lambda x: getsize(x), filepaths))

    with ProgressFileObject(dir, total_size, filepaths) as sfr:
        with tarfile.open(fileobj=sfr, mode="r:bz2") as tar:
            tar.extractall(path=dirpath)
