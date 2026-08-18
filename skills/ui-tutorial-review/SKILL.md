# Software and UI tutorial review

Use this after `watch-review` when a tutorial or screen recording should demonstrate a
known sequence. Adapt the JSON example into an ordered step checklist, then run:

```powershell
toolbox review tutorial outputs/tutorial-review.json --steps tutorial-steps.json --output outputs/tutorial-verification.json
```

Each result cites the timestamp that supports the step. Missing evidence becomes
`NEEDS_HUMAN_REVIEW`; evidence that appears only before an already-verified later step is
`OUT_OF_ORDER`. No model, cloud service, or visual inference is used.
