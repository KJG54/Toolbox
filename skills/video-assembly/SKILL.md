# Video assembly

Join local clips in the supplied order into a portable MP4:

```powershell
toolbox video assemble intro.mp4 main.mp4 outro.mp4 --output outputs/final.mp4
```

Every clip must contain video and audio. The output is re-encoded for portability; sources are not
modified and no media is uploaded.
