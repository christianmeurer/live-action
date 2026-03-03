# GPU Ops Mode Rules

- Optimize for one active GPU inference job at a time.
- Prefer bf16/fp8-capable execution paths and deterministic seeds.
- Before tuning, collect baseline metrics (latency, peak memory, throughput).
- Apply one optimization change per run and measure deltas.
- For OOM, reduce workload in this order: resolution, chunk size, batch size, then offload.

