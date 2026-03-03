# Debug Mode Rules

- Reproduce first, patch second.
- Classify failures: OOM, dependency/runtime, data/validation, logic.
- For OOM, lower pressure deterministically (batch/chunk/resolution/offload), then retry.
- Record exact command/config/state for every reproduction.
- Attach before/after measurements for each fix attempt.

