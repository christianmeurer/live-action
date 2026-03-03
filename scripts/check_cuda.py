from __future__ import annotations


def main() -> None:
    try:
        import torch  # type: ignore
    except Exception:
        print("torch unavailable")
        return

    if not torch.cuda.is_available():
        print("cuda unavailable")
        return

    print(torch.cuda.get_device_name(0))


if __name__ == "__main__":
    main()

