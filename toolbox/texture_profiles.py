"""Local game texture export profiles."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from PIL import Image
class TextureProfileError(ValueError): pass
_PROFILES={"mobile":(1024,".webp"),"desktop":(2048,".webp"),"game-hd":(4096,".png"),"godot-mobile":(1024,".png"),"godot-desktop":(2048,".png")}
def export_texture_profile(source: Path, output: Path, *, profile: str, overwrite: bool=False) -> dict[str,Any]:
    source=source.resolve(); output=output.resolve(); profile=profile.casefold()
    if profile not in _PROFILES: raise TextureProfileError("profile must be mobile, desktop, game-hd, godot-mobile, or godot-desktop")
    if not source.is_file(): raise FileNotFoundError(f"Texture source does not exist: {source}")
    if source==output: raise TextureProfileError("Output must differ from source")
    if output.suffix.casefold()!=_PROFILES[profile][1]: raise TextureProfileError(f"{profile} profile output must use {_PROFILES[profile][1]}")
    if output.exists() and not overwrite: raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    max_size,_=_PROFILES[profile]
    with Image.open(source) as im:
        image=im.convert("RGBA")
        scale=min(1,max_size/max(image.width,image.height)); width=max(1,round(image.width*scale)); height=max(1,round(image.height*scale))
        if (width,height)!=image.size: image=image.resize((width,height),Image.Resampling.LANCZOS)
        if output.suffix.casefold()==".webp": image.save(output,quality=90,method=6)
        else: image.save(output)
    return {"format":"toolbox-texture-profile/v1","source":str(source),"output":str(output),"profile":profile,"size":[width,height],"execution":"local_only"}
