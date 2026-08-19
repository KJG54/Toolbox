# Godot import profiles

Create a source-preserving PNG texture derivative for a Godot project, then use the local import map for its expected `res://` path:

```powershell
toolbox texture export-profile texture.png --profile godot-mobile --output outputs/texture.png
toolbox game godot-import-map my-godot-game
```

Toolbox does not create Godot import metadata; the installed editor owns that step.
