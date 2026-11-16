"""Gemeinsame Pfade und Helfer fuer die Pruefskripte der A2-Gegenpruefung (2026-11-16).

Alle Skripte lesen die Leiterplatte nur. Experimente, die etwas veraendern, arbeiten
auf einer temporaeren Kopie des KiCad-Projekts. Umgebungsvariablen:
  PMU_PCB   Pfad zu einer anderen .kicad_pcb
  PMU_OUT   Ausgabeverzeichnis (Standard: ../daten)
pcbnew-Skripte mit dem Python aufrufen, das das KiCad-Modul hat (Linux: /usr/bin/python3).
"""
import os, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PMU = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
A2 = os.path.join(PMU, "rev-a2-layout-280x260")
KICAD_DIR = os.path.join(A2, "kicad")
PCB = os.environ.get("PMU_PCB", os.path.join(KICAD_DIR, "HomeMy_PMU_RevA.kicad_pcb"))
SCH = os.path.join(os.path.dirname(PCB), "HomeMy_PMU_RevA.kicad_sch")
OUT = os.environ.get("PMU_OUT", os.path.join(HERE, "..", "daten"))
BUSBAR_JSON = os.path.join(A2, "manufacturing", "busbar-pcb-interface.json")

POWER_NETS = {"BATT_FUSED_P", "BATT_SENSED_P", "MAIN_COMMON", "BATT_N", "SYS_BUS_P",
              "MOTION_SENSED_P", "MOTION_COMMON", "MOTION_BUS_P", "ARM_L_N", "ARM_R_N"}


def project_copy():
    """Kopiert das KiCad-Projekt der gewaehlten PCB in ein temporaeres Verzeichnis."""
    tmp = tempfile.mkdtemp(prefix="pmu-a2-")
    dst = os.path.join(tmp, "kicad")
    shutil.copytree(os.path.dirname(PCB), dst)
    return dst, os.path.join(dst, os.path.basename(PCB))


def kicad_cli(*args, cwd=None):
    env = dict(os.environ)
    env.setdefault("HOME", tempfile.gettempdir())
    return subprocess.run(["kicad-cli", *args], cwd=cwd, env=env, capture_output=True, text=True)


def export_netlist(path=None):
    path = path or os.path.join(tempfile.mkdtemp(prefix="pmu-net-"), "netlist.xml")
    r = kicad_cli("sch", "export", "netlist", "--format", "kicadxml", "-o", path, SCH)
    if not os.path.exists(path):
        raise SystemExit("Netzlistenexport fehlgeschlagen: " + r.stderr)
    return path
