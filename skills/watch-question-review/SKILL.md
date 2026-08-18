# Question-directed Watch review

Use this after `watch-review` when you need to locate a tutorial step, UI state, gameplay
event, or spoken explanation without processing the original video again.

```powershell
toolbox review ask outputs/recording-review.json "When does the setting change?"
```

The result is extractive and local: it cites matching transcript or OCR evidence and says
when the saved timeline does not contain enough evidence. It does not call a model, upload
media, or infer unseen visual content.
