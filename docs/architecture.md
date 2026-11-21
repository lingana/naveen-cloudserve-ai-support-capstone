# Architecture

The pipeline processes tickets in this order:

1. Ingest: normalize one of four channels.
2. Classify: produce intent, urgency, confidence and alternatives.
3. Retrieve: search supplied documentation with a relevance threshold.
4. Route: apply hard policies and a deterministic confidence threshold.
5. Generate: draft a cited answer or escalate.
6. Validate: block private data, unsupported commitments and invented citations.
7. Persist: write a reconstructable SQLite decision record.

Cross-cutting concerns are configuration, deterministic decision logging, monitoring and failure fallback. External model access is not required for the development harness; the generation component is intentionally conservative and source-grounded.
