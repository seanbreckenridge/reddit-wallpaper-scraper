"""
Recursively searches ./wallpapers for images
Classify each image into

    width / height <= 0.8 into ./mobile.txt
    0.8 > width / height <= 1.2 into ./square.txt
    width / height > 1.3 into ./landscape.txt

"""

import os
import sys
import argparse
import time
from pathlib import Path

import click
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("--link-files", help="hardlink each file from ./wallpapers to its own directory type (mobile/square/landscape)", action="store_true", default=False, required=False)
args = parser.parse_args()
print(args)

mobile = []
square = []
landscape = []

for path in Path(os.path.join(os.path.dirname(__file__), 'wallpapers')).rglob('*'):
    if os.path.isfile(path):
        _, ext = os.path.splitext(path)
        if ext in [".gif", ".mp4"]:
            click.secho("Ignoring video/gif: {}".format(path), fg='yellow')
        else:
            try:
                img_obj = Image.open(path)
                width_height_ratio = img_obj.width / img_obj.height
                if width_height_ratio <= 0.7:
                    mobile.append(path)
                elif width_height_ratio <= 1.3:
                    square.append(path)
                else:
                    landscape.append(path)
            except:
                print(f"Couldnt load file {path}")

print(f"Mobile: {len(mobile)}")
print(f"Square: {len(square)}")
print(f"Landscape: {len(landscape)}")

for name, arr in [("mobile", mobile), ("square", square), ("landscape", landscape)]:
    with open(f'{name}.txt', 'w') as f:
        f.write("\n".join(map(str, arr)))
    if args.link_files:
        dir_name = os.path.join(os.path.dirname(__file__), name)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        for filepath in arr:
            target_filepath = os.path.join(dir_name, os.path.basename(filepath))
            if os.path.exists(target_filepath):  # name conflict
                target_filepath = f"{target_filepath}_{time.time()}"
            # print(f"Linking {filepath} to {target_filepath}")
            os.link(filepath, target_filepath)
