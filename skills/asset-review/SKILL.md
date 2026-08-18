# Evidence-based asset review

Use this after `watch-review` when a render, turntable, UI capture, or gameplay clip has
clear acceptance criteria. Create a JSON criteria file from the example, then run:

```powershell
toolbox review assess outputs/asset-review.json --criteria criteria.json --output outputs/asset-assessment.json
```

The report is deliberately conservative: matching transcript/OCR evidence can pass a
criterion, forbidden evidence can fail it, and absent evidence becomes `NEEDS_HUMAN_REVIEW`.
It never claims visual verification from frames that have not been described locally.
