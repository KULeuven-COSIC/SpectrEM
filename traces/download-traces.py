# Script to download the pre-recorded SpectrEM traces
#
# This file interfaces with the API provided by KU Leuven RDR to autimatically
# download the pre-recorded traces.
#
# Last modified: 2023-06-19

import requests
from tqdm import tqdm
import os

q = "https://rdr.kuleuven.be/api/datasets/:persistentId/?persistentId=doi:10.48804/AHTI1A"
headers = {}

# https://stackoverflow.com/a/16696317
def download_file(url, local_filename, i, tot):
    os.makedirs(os.path.dirname(local_filename), exist_ok=True)  # Make sure the directory exists
    with requests.get(url, stream=True, headers=headers) as r:
        r.raise_for_status()
        size = int(r.raw.headers.get('Content-Length'))
        with tqdm(total=size, desc=f"({i+1}/{tot}) {local_filename}", unit="B", unit_scale=True) as pbar:
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=16384): 
                    f.write(chunk)
                    pbar.update(min(16384, size - pbar.n))

# Access list of files
r = requests.get(q)

if r.status_code != 200:
    print("This dataset is not yet publicly released, but will be in the near future. Please enter your API key if you have access to the draft dataset.")
    api_key = input("API key: ")

    headers = {'X-Dataverse-key': api_key}
    r = requests.get(q, headers=headers)

    if r.status_code != 200:
        print("Invalid API key.")
        exit()

files = r.json()["data"]["latestVersion"]["files"]

dirs = dict({x["directoryLabel"].split("/")[0]:0 for x in files if "directoryLabel" in x})


print("This dataset contains the following directories:")
for dir in sorted(dirs):
    dirs[dir] = sum(map(lambda x: x["dataFile"]["filesize"] if "directoryLabel" in x and x["directoryLabel"].startswith(dir) else 0, files))

    print(f"  {dir:25s} {dirs[dir]/1e9:06.3f} GB")


print("\nPlease specify which directories to download:")
files_to_download = dict()
total_size = 0

for dir in sorted(dirs):
    y = input(f"  {dir:25s} ({dirs[dir]/1e9:06.3f} GB) [y/n]: ")

    if y.lower() == "y":
        files_to_download |= {f"{x['directoryLabel']}/{x['label']}": x["dataFile"]["id"] for x in files if "directoryLabel" in x and x["directoryLabel"].startswith(dir)}
        total_size += dirs[dir]


print(f"\nDownload size: {total_size/1e9:.3f} GB")
print(f"Files will be placed in the following directory: {os.getcwd()}")
y = input("Proceed [y/n]? ")

if y.lower() != "y":
    exit()

print()
for i, file in enumerate(sorted(files_to_download)):
    download_file(f"https://rdr.kuleuven.be/api/access/datafile/{files_to_download[file]}", file, i, len(files_to_download))
