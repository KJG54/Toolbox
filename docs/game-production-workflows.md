# Local Game Production Workflows

These workflows implement the current game-creation batch. They are
local-first: no command logs into a generation service, uploads media, calls an
API, buys credits, or publishes an artifact.

## 1. Record an external generation after it is downloaded

Use this only after the owner has approved the provider and media sent to it.
It records the provider, plan, terms URL, release status, and a prompt
reference in the normal local provenance sidecar. It does not contact the
provider.

```powershell
toolbox provenance external .\asset.glb `
  --provider Meshy --plan Free `
  --terms-url https://www.meshy.ai/pricing `
  --output-status ATTRIBUTION_REQUIRED `
  --prompt-reference "local-design-note-042" `
  --source .\reference.png
```

`DRAFT_ONLY` and `PERSONAL_ONLY` never qualify for release. Use
`RELEASE_APPROVED` only after a human has reviewed the exact plan, terms, and
asset provenance.

## 2. Plan local 3D remediation

```powershell
toolbox game 3d-remediation-plan .\asset.glb --output .\reports\asset-3d-plan.json
```

The report requires local inspection before an asset is used in a game or sent
to a 3D printer: scale, topology, UVs, materials, collision/LOD, licensing, and
printability are not inferred from generation success.

## 3. Plan a game audio package

```powershell
toolbox game audio-package-plan .\audio --output .\reports\audio-package.json
```

Use its report with the existing local `toolbox audio clean`, `mix`, and
`assemble` commands to create reviewed WAV/OGG derivatives. The plan checks
that each source has a sidecar; it does not transform audio itself.

## 4. Scaffold a Godot vertical slice

```powershell
toolbox game godot-vertical-slice --output .\prototype --name "My Prototype"
```

The scaffold creates a minimal project, a `CharacterBody2D` player script, and
a checklist for input actions, an interaction, UI, music/SFX, and gameplay
evidence. It does not launch Godot or assume a Godot installation; configure
the input actions and validate the scene in a locally installed editor.

## 5. Scaffold a release and marketing pack

```powershell
toolbox game release-pack --output .\release-pack --name "My Prototype"
```

It creates folders for screenshots, trailer sources/finals, social media,
store assets, subtitles, and metadata. It never packages or publishes. Use
`toolbox delivery audit` only after provenance and owner review are complete.

## Suggested flow

1. Acquire or create an approved local asset.
2. Record external-generation metadata when applicable.
3. Run the 3D/audio plan and complete local remediation.
4. Add the reviewed assets to a Godot vertical slice and capture evidence.
5. Assemble a release pack, audit it locally, then request separate approval to
   package or publish.
