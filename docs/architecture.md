# Architecture

The registry describes available capabilities and their constraints. Runtime detection is
separate and read-only: a tool can be cataloged without being installed. The router applies
license, privacy, format, local-only, hardware, and installed-state gates before ranking.

Watch remains an independently testable component. Its adapter exposes the existing video
watching, transcription, scene detection, evidence, and visual-QA capabilities without
duplicating Watch internals. Future Watch work adds a timeline façade and specialized modes
on top of its cached evidence, never a remote-compute route.
