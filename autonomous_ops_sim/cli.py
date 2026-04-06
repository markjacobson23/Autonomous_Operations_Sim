import argparse

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autonomous-ops-sim",
        description="A Python simulator for autonomous operations research and development.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="autonomous-ops-sim 0.1.0",
    )
    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())