# Game asset manifests

Hash local game assets before and after a change, then compare the saved manifests:

```powershell
toolbox game manifest assets --output outputs/before.json
toolbox game compare-manifests outputs/before.json outputs/after.json
```
