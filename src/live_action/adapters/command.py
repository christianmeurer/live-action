from __future__ import annotations

import subprocess


def render_command(template: list[str], variables: dict[str, str]) -> list[str]:
    rendered: list[str] = []
    for token in template:
        updated = token
        for key, value in variables.items():
            updated = updated.replace(f"{{{key}}}", value)
        rendered.append(updated)
    return rendered


def run_command(command: list[str], stage: str) -> None:
    try:
        subprocess.run(command, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr or ""
        stdout = exc.stdout or ""
        msg = f"{stage} command failed: {' '.join(command)} stdout={stdout.strip()} stderr={stderr.strip()}"
        raise RuntimeError(msg) from exc

