# Semantic image understanding review

Approved local runtime: **Microsoft Florence-2 Base**, pinned to revision
`5ca5edf5bd017b9919c05d08aebef5e4c7ac3bac`. It supports captions, detailed captions, and object
detection for a local image. The model files and reviewed runtime code are cached locally; requests
use `local_files_only=True` and do not upload media or call a cloud inference API.

## What to review

1. [Model card](https://huggingface.co/microsoft/Florence-2-base) — intended capabilities, local
   runtime instructions, and model size.
2. [License](https://huggingface.co/microsoft/Florence-2-base/blob/main/LICENSE) — MIT license.
3. Runtime code fetched by the published instructions:
   [configuration](https://huggingface.co/microsoft/Florence-2-base/blob/main/configuration_florence2.py),
   [model implementation](https://huggingface.co/microsoft/Florence-2-base/blob/main/modeling_florence2.py), and
   [processor](https://huggingface.co/microsoft/Florence-2-base/blob/main/processing_florence2.py).

## Approval decision

Approval authorized a local installation of the reviewed runtime code, PyTorch and Transformers
dependencies, and the model files into the local cache. The first cache download contacted Hugging
Face; normal Toolbox requests cannot download a model. Toolbox returns the pinned version with every
result so its use can be recorded in provenance.

The model requires `trust_remote_code=True`; its configuration, model implementation, and processor
were inspected before approval. The installed PyTorch build currently has no CUDA access, so the
current environment uses CPU execution and is expected to be `LOCAL_SLOW` for larger images. A
working local CUDA build and GPU access would improve performance; Toolbox will not offer remote
execution as a fallback.
