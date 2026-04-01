"""Convert openapi.yaml next to this script into swagger.json (OpenAPI 3 JSON)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    try:
        import yaml
    except ImportError:
        print("PyYAML required: pip install pyyaml", file=sys.stderr)
        return 1
    src = HERE / "openapi.yaml"
    out = HERE / "swagger.json"
    data = yaml.safe_load(src.read_text(encoding="utf-8"))
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
