# Local text to speech

Create a local WAV derivative from supplied text:

```powershell
toolbox tts speak "Release candidate is ready for review." --output outputs/review.wav
```

This uses the local Windows Speech API and writes provenance beside the output. It must not fall
back to an online voice service. If Windows reports that the speech service is unavailable, report
that environment condition and keep the original text unchanged.
