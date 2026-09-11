"""Bounded native checks. No CAD writes, rule changes, or implicit successful exits."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "bounded-ledger.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def minutes(ledger):
    return (datetime.now(timezone.utc) - datetime.fromisoformat(ledger["started_utc"])).total_seconds() / 60


def input_hashes(board):
    inputs = [board, board.with_suffix('.kicad_pro'), board.with_suffix('.kicad_dru')]
    inputs += [board.with_suffix('.kicad_sch')] + [p for p in board.parent.glob('*.kicad_sch') if not p.name.startswith('HomeMy_PMU_RevA_')]
    inputs += list(board.parent.glob('*-lib-table'))
    base = ROOT.parent / 'rev-a/kicad'
    inputs += [base / 'PMU_RevA.kicad_sym'] + list((base / 'libraries').rglob('*.kicad_mod'))
    return {str(p.relative_to(ROOT.parent)).replace('\\', '/'): sha(p) for p in inputs}


def check(board, phase, only="both", timeout=180):
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    if minutes(ledger) >= 140 or ledger.get("stop_required"):
        raise RuntimeError("Hard stopping boundary reached; save/document only")
    before = input_hashes(board)
    results = {}
    for name, domain, suffix in [("erc", "sch", ".kicad_sch"), ("drc", "pcb", ".kicad_pcb")]:
        if only not in ("both", name):
            continue
        if minutes(ledger) >= 140:
            raise RuntimeError("140-minute stop boundary reached")
        if name == "drc":
            if ledger["native_drc_calls"] >= 8:
                raise RuntimeError("Eight native DRC calls already used")
            ledger["native_drc_calls"] += 1
        target = ROOT.parents[3] / "tools-local" / "bounded-shrink-native"
        target.mkdir(parents=True, exist_ok=True)
        out = target / (board.stem + "-" + phase + "-" + name + ".json")
        if out.exists():
            raise RuntimeError("Refusing to overwrite an earlier native report")
        command = [r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe", domain, name,
                   "--format", "json", "--severity-all", "--exit-code-violations", "--output", str(out)]
        if name == "drc":
            command += ["--all-track-errors", "--schematic-parity"]
        command += [str(board.with_suffix(suffix))]
        event = {"kind": name, "phase": phase, "board_sha256": sha(board),
                 "started_utc": datetime.now(timezone.utc).isoformat(), "command": command}
        ledger["native_calls"].append(event)
        write(LEDGER, ledger)
        start = time.monotonic()
        try:
            result = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=timeout)
            code, output = result.returncode, result.stdout + result.stderr
        except subprocess.TimeoutExpired as exc:
            code, output = 124, "Native process timeout; no successful exit."
        event.update(exit_code=code, seconds=round(time.monotonic() - start, 3))
        # Exit 5 is KiCad's normal violation result, not a process crash.
        crash = code not in (0, 5)
        signature = "timeout" if code == 124 else str(code)
        if crash:
            previous = ledger.get("last_native_failure")
            ledger["identical_native_failures"] = ledger.get("identical_native_failures", 0) + 1 if previous == signature else 1
            ledger["last_native_failure"] = signature
            if ledger["identical_native_failures"] >= 2:
                ledger["stop_required"] = "two_identical_native_failures"
        else:
            ledger["identical_native_failures"] = 0
        value = {"process_exit_code": code, "process_normal": code in (0, 5),
                 "passed": False, "report_complete": False, "input_hashes_sha256": before,
                 "wall_seconds": event["seconds"], "process_output": output[-6000:]}
        if out.exists():
            raw = json.loads(out.read_text(encoding="utf-8"))
            required = ['sheets', '$schema'] if name == 'erc' else ['violations', 'unconnected_items', 'schematic_parity', '$schema']
            valid = all(k in raw for k in required)
            valid = valid and raw.get('$schema') == 'https://schemas.kicad.org/'+name+'.v1.json'
            if not valid:
                raise RuntimeError('Native report lacks required schema/fields')
            rows = raw.get("violations", [])
            if name == "erc":
                rows = [r for sheet in raw.get("sheets", []) for r in sheet.get("violations", [])]
            counts = Counter((r["type"], r["severity"]) for r in rows)
            capped = any(n >= 199 for n in counts.values()) or len(raw.get('unconnected_items', [])) >= 499
            value.update(report_complete=code in (0, 5), report_parsed=True, counts_may_be_capped=capped, report_sha256=sha(out), native_report=raw,
                         counts=[{"type": k[0], "severity": k[1], "count": n} for k, n in sorted(counts.items())],
                         open_connections=len(raw.get("unconnected_items", [])),
                         parity_findings=len(raw.get("schematic_parity", [])))
            value["passed"] = code == 0 and not rows and not value["open_connections"] and not value["parity_findings"]
        event["report_sha256"] = value.get("report_sha256")
        write(LEDGER, ledger)
        results[name] = value
        print(name, phase, code, value.get("counts"), "opens", value.get("open_connections"), flush=True)
        if ledger.get("stop_required"):
            break
    if input_hashes(board) != before:
        raise RuntimeError("Native check changed CAD input")
    dest = ROOT / "results" / (board.stem + ".json")
    dest.parent.mkdir(exist_ok=True)
    summary = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else {"board": str(board.relative_to(ROOT)), "checks": {}}
    summary["checks"][phase] = results
    write(dest, summary)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("phase")
    parser.add_argument("--only", choices=["both", "erc", "drc"], default="both")
    args = parser.parse_args()
    check(args.board.resolve(), args.phase, args.only)
