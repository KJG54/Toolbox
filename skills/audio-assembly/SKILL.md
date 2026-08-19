# Audio assembly

Concatenate local narration or sound-effect clips in the supplied order:

```powershell
toolbox audio assemble intro.wav narration.wav outro.wav --output outputs/track.wav
```

The workflow creates a separate derivative and normalizes it by default. It does not synthesize,
repair, or otherwise generate audio.
