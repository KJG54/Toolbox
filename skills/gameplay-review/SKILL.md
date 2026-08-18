# Gameplay review

Use this after `watch-review` to verify expected objectives, HUD states, scripted moments,
or failures from local transcript/OCR evidence.

```powershell
toolbox review gameplay outputs/playthrough-review.json --events gameplay-events.json --output outputs/gameplay-review.json
```

The event file uses `toolbox-gameplay-events/v1` and supports required, optional-any, and
forbidden terms. Visual-only events without local evidence become `NEEDS_HUMAN_REVIEW`.
