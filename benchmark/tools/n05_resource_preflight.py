"""Resource preflight for N-05 formal benchmark attempts.

This guard is intentionally outside timed samples. It prevents a formal run from
starting on a volume that lacks the disk headroom required by the accepted
Reference Workstation policy after the 2026-10-23 disk-full abort.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIN_FREE_DISK_GIB = 32
MIN_FREE_DISK_BYTES = MIN_FREE_DISK_GIB * 1024**3
DEFAULT_QDRANT_ROOT = Path(r"C:\Qdrant\SGOKB")
PLANNED_FORMAL_SAMPLES = 46
QDRANT_DEFAULT_WAL_CAPACITY_MB = 32


def _capture_powershell(script: str) -> dict:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        return {
            "available": False,
            "return_code": completed.returncode,
            "stderr": completed.stderr.strip(),
        }
    try:
        return {"available": True, "value": json.loads(completed.stdout)}
    except json.JSONDecodeError:
        return {
            "available": False,
            "return_code": completed.returncode,
            "stderr": "PowerShell returned non-JSON output",
        }


def _volume(path: Path) -> dict:
    resolved = path.resolve()
    usage = shutil.disk_usage(resolved)
    return {
        "path": str(resolved),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "free_gib": usage.free / 1024**3,
        "required_free_gib": MIN_FREE_DISK_GIB,
        "pass": usage.free >= MIN_FREE_DISK_BYTES,
    }


def _windows_memory() -> dict:
    script = r"""
$o = Get-CimInstance Win32_OperatingSystem
$p = Get-CimInstance Win32_PageFileUsage |
  Select-Object Name,AllocatedBaseSize,CurrentUsage,PeakUsage
@{
  total_visible_kib = [int64]$o.TotalVisibleMemorySize
  free_physical_kib = [int64]$o.FreePhysicalMemory
  total_virtual_kib = [int64]$o.TotalVirtualMemorySize
  free_virtual_kib = [int64]$o.FreeVirtualMemory
  pagefiles = @($p)
} | ConvertTo-Json -Depth 4 -Compress
"""
    return _capture_powershell(script)


def evaluate(repo_root: Path, qdrant_root: Path) -> dict:
    if not repo_root.exists():
        raise FileNotFoundError(repo_root)
    if not qdrant_root.exists():
        raise FileNotFoundError(qdrant_root)

    repo = _volume(repo_root)
    qdrant = _volume(qdrant_root)
    volumes = {repo["path"]: repo, qdrant["path"]: qdrant}
    passed = all(item["pass"] for item in volumes.values())
    return {
        "status": "PASS" if passed else "BLOCKED_DISK_HEADROOM",
        "policy": {
            "minimum_free_disk_gib": MIN_FREE_DISK_GIB,
            "scope": "every volume hosting the repository/run evidence or active Qdrant runtime",
            "formal_samples": PLANNED_FORMAL_SAMPLES,
            "qdrant_default_wal_capacity_mb": QDRANT_DEFAULT_WAL_CAPACITY_MB,
            "nominal_wal_capacity_mb_if_one_default_segment_per_sample_collection": (
                PLANNED_FORMAL_SAMPLES * QDRANT_DEFAULT_WAL_CAPACITY_MB
            ),
            "note": (
                "32 GiB is an SGOKB Reference Workstation safety gate, not a Qdrant product "
                "minimum. It reserves room for benchmark artifacts, Qdrant WAL/temp/optimizer "
                "work, and Windows page-file growth under the observed long-Harrier commit load."
            ),
        },
        "repository_volume": repo,
        "qdrant_volume": qdrant,
        "windows_memory": _windows_memory(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--qdrant-root", type=Path, default=DEFAULT_QDRANT_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(args.repo_root, args.qdrant_root)
    except Exception as exc:
        result = {
            "status": "BLOCKED_RESOURCE_PREFLIGHT",
            "error": f"{type(exc).__name__}: {exc}",
        }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
