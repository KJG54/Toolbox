"""Local narration and music-bed mixing with gain, fades, and ducking."""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import Any
from .audio_cleanup import AudioCleanupError
from .media import _binary, probe_media
def mix_audio(narration: Path, bed: Path, output: Path, *, narration_gain_db: float=0, bed_gain_db: float=-18, fade_seconds: float=0.5, ducking: bool=True, overwrite: bool=False)->dict[str,Any]:
    narration=narration.resolve(); bed=bed.resolve(); output=output.resolve()
    if not narration.is_file() or not bed.is_file(): raise FileNotFoundError("Narration and bed audio sources must exist")
    if output in {narration,bed}: raise AudioCleanupError("Output must differ from input sources")
    if output.suffix.casefold() not in {".wav",".mp3",".flac"}: raise AudioCleanupError("Mix output must use .wav, .mp3, or .flac")
    if output.exists() and not overwrite: raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    if fade_seconds<0: raise AudioCleanupError("fade_seconds must be zero or greater")
    for source in (narration,bed):
        if not any(s.get("codec_type")=="audio" for s in probe_media(source).get("streams",[])): raise AudioCleanupError(f"Source has no audio stream: {source.name}")
    output.parent.mkdir(parents=True,exist_ok=True); filter=f"[0:a]volume={narration_gain_db}dB[n];[1:a]volume={bed_gain_db}dB[b];"
    filter += "[b][n]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=500[d];" if ducking else "[b]anull[d];"
    filter += "[d][n]amix=inputs=2:duration=longest,afade=t=in:st=0:d="+str(fade_seconds)+"[mix]"
    cmd=[_binary("ffmpeg"),"-hide_banner","-loglevel","error","-y" if overwrite else "-n","-i",str(narration),"-i",str(bed),"-filter_complex",filter,"-map","[mix]"]
    cmd += ["-c:a","pcm_s16le"] if output.suffix.casefold()==".wav" else ["-c:a","libmp3lame","-q:a","2"] if output.suffix.casefold()==".mp3" else ["-c:a","flac"]
    cmd.append(str(output)); done=subprocess.run(cmd,text=True,capture_output=True,check=False)
    if done.returncode or not output.is_file() or not output.stat().st_size: raise AudioCleanupError(f"ffmpeg could not mix audio: {done.stderr.strip()[-1000:]}")
    return {"format":"toolbox-audio-mix/v1","narration":str(narration),"bed":str(bed),"output":str(output),"ducking":ducking,"execution":"local_only"}
