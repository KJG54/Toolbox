# Generation decisions

## ACE-Step 1.5

Approved and installed as a local-only music component at `components/ace-step`.
Toolbox records source revision `14c0211d5a0653b0f63e27686f4c3f151b4d8629` and the MIT
model card at <https://huggingface.co/ACE-Step/Ace-Step1.5>. The local RTX 2060 profile is
`acestep-v15-turbo` with the language model disabled, INT8 weight quantization, eager attention,
and CPU/DiT offload. It initializes successfully but is expected to be slow.

The local source, virtual environment, and checkpoints are machine state and intentionally ignored
by Git. Do not enable an LM, download XL variants, or route to cloud inference without a separate
review and approval.

## AI SFX

Deferred by the owner. Use Toolbox procedural SFX unless a future explicit approval selects and
reviews an AI SFX candidate.

## FLUX.1 Schnell

Deferred by the owner. Use an approved secondary image-generation source instead; do not download
or install FLUX locally on the current 6 GB GPU.
