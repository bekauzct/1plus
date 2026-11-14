"""tests/fixtures/js_golden.json ni prototip JS'dan (node) qayta hosil qiladi.

uv run python scripts/gen_golden.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.golden_cases import build_cases  # noqa: E402


def run_js(cases: list[dict]) -> list:
    proc = subprocess.run(
        ["node", str(ROOT / "scripts" / "js_reference.mjs")],
        input=json.dumps(cases, ensure_ascii=False),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def main() -> None:
    cases = build_cases()
    results = run_js(cases)
    out = [{"fn": c["fn"], "args": c["args"], "expected": r} for c, r in zip(cases, results, strict=True)]
    path = ROOT / "tests" / "fixtures" / "js_golden.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(out)} ta holat yozildi: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
