from __future__ import annotations

from live_action.preprocess.ffmpeg import ensure_ffmpeg


def main() -> None:
    ensure_ffmpeg()
    print("ffmpeg and ffprobe available")


if __name__ == "__main__":
    main()

