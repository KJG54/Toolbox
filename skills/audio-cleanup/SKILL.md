# Audio cleanup

Create a derivative with optional trim and EBU-style loudness normalization:

```powershell
toolbox audio clean input.wav --output outputs/input-clean.wav
```

This is an FFmpeg workflow that does not modify the input or invoke a cloud service. It does not
claim to remove noise, repair speech, or generate audio content.
