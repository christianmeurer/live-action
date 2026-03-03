# Architect Mode Rules

- Define milestones as executable slices.
- Every plan must include acceptance criteria and rollback notes.
- Prefer deterministic workflows and explicit artifact paths.
- Design for single-GPU serialized execution (no overlapping heavy jobs).
- For model-stage plans, always include memory budget assumptions.

