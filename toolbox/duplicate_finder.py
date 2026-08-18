"""Local exact and perceptual duplicate discovery."""
from __future__ import annotations
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Any
from PIL import Image
import imagehash

_IMAGES={".png",".jpg",".jpeg",".webp",".bmp",".tiff"}
def find_duplicates(directory: Path, *, threshold: int=4, max_files: int=10000) -> dict[str, Any]:
    directory=directory.resolve()
    if not directory.is_dir(): raise FileNotFoundError(f"Asset directory does not exist: {directory}")
    if not 0<=threshold<=32 or not 1<=max_files<=100000: raise ValueError("threshold must be 0-32 and max_files must be 1-100000")
    files=[p for p in directory.rglob("*") if p.is_file() and not p.name.endswith(".provenance.json")]
    if len(files)>max_files: raise ValueError(f"Found {len(files)} files; narrow the directory or raise --max-files")
    exact=defaultdict(list); images=[]
    for p in files:
        digest=hashlib.sha256(p.read_bytes()).hexdigest(); exact[digest].append(p.relative_to(directory).as_posix())
        if p.suffix.casefold() in _IMAGES:
            try:
                with Image.open(p) as im: images.append((p.relative_to(directory).as_posix(), imagehash.phash(im.convert("RGB"))))
            except OSError: pass
    near=[]
    for i,(left,left_hash) in enumerate(images):
        for right,right_hash in images[i+1:]:
            distance=left_hash-right_hash
            if distance<=threshold: near.append({"left":left,"right":right,"distance":distance})
    return {"format":"toolbox-duplicate-report/v1","directory":str(directory),"exact_duplicates":[{"sha256":digest,"paths":paths} for digest,paths in exact.items() if len(paths)>1],"near_duplicate_images":near,"threshold":threshold,"execution":"local_only","mutations_performed":[]}
