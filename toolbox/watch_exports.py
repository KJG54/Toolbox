"""Local subtitle and chapter exports from saved Watch timelines."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from .timeline_review import TimelineReviewError, load_timeline
def _time(seconds: float, *, vtt: bool=False)->str:
    total=max(0,float(seconds)); hours=int(total//3600); minutes=int(total%3600//60); secs=total%60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", "." if vtt else ",")
def export_subtitles(timeline_path: Path, output: Path, *, overwrite: bool=False)->dict[str,Any]:
    timeline=load_timeline(timeline_path); output=output.resolve(); ext=output.suffix.casefold()
    if ext not in {".srt",".vtt"}: raise TimelineReviewError("Subtitle output must use .srt or .vtt")
    if output.exists() and not overwrite: raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    segments=[item for item in timeline.get("transcript",{}).get("segments",[]) if str(item.get("text","")).strip()]
    vtt=ext==".vtt"; lines=["WEBVTT",""] if vtt else []
    for index,item in enumerate(segments,1):
        if not vtt: lines.append(str(index))
        lines.extend([f"{_time(item['start_seconds'],vtt=vtt)} --> {_time(item['end_seconds'],vtt=vtt)}",str(item['text']).strip(),""])
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text("\n".join(lines),encoding="utf-8")
    return {"format":"toolbox-watch-subtitles/v1","timeline":str(timeline_path.resolve()),"output":str(output),"segments":len(segments),"execution":"local_only"}
def export_chapters(timeline_path: Path, output: Path, *, overwrite: bool=False)->dict[str,Any]:
    timeline=load_timeline(timeline_path); output=output.resolve()
    if output.suffix.casefold()!=".ffmeta": raise TimelineReviewError("Chapter output must use .ffmeta")
    if output.exists() and not overwrite: raise FileExistsError(f"Output already exists: {output}; use --force to replace it")
    stamps=sorted({round(float(frame["timestamp_seconds"]),3) for frame in timeline.get("perception",{}).get("frames",[])})
    duration=float(timeline.get("metadata",{}).get("duration_seconds",0)); lines=[";FFMETADATA1"]
    for index,start in enumerate(stamps):
        end=stamps[index+1] if index+1<len(stamps) else duration
        if end<=start: continue
        lines.extend(["[CHAPTER]","TIMEBASE=1/1000",f"START={round(start*1000)}",f"END={round(end*1000)}",f"title=Scene {index+1}"])
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return {"format":"toolbox-watch-chapters/v1","timeline":str(timeline_path.resolve()),"output":str(output),"chapters":len(stamps),"execution":"local_only"}
