#!/usr/bin/python3
"""Native KiCad-Pruefungen und zwei Experimente auf temporaeren Projektkopien (Original bleibt unveraendert).

Aufruf: /usr/bin/python3 drc_experiments.py [native] [hv] [power]
  native  ERC, DRC wie gespeichert und DRC mit neu gefuellten Zonen (jeweils alle Schweregrade, Paritaet)
  hv      Zusatzregel "42-V-Netze zu allen anderen Netzen >= 0,6 mm" -> Liste aller engeren Stellen
  power   entfernt aus den Hochstromnetzen alle Leiterbahnen < 1,0 mm und Vias < 0,8/0,4 mm und prueft,
          welche Pads dann nicht mehr verbunden sind (zeigt, was nur an duennen Abgriffen haengt)
Ergebnisse: daten/native_checks.json, daten/hv_clearance.json, daten/power_continuity.json
"""
import collections, json, os, re, sys
import _common as C

HV_EXACT = {"BATT_FUSED_P", "BATT_SENSED_P", "MAIN_COMMON", "SYS_BUS_P", "MOTION_SENSED_P", "MOTION_COMMON",
            "MOTION_BUS_P", "MAIN_KELVIN_P", "MAIN_KELVIN_N", "MAIN_CS_P", "MAIN_ISCP", "MAIN_CAP", "MAIN_HGATE",
            "MAIN_DGATE", "MOTION_KELVIN_P", "MOTION_KELVIN_N", "MOTION_CS_P", "MOTION_ISCP", "MOTION_BST",
            "MOTION_PU", "MOTION_GATE_DRIVE", "INA_IN_P", "INA_IN_N", "INA_VBUS", "PC_BUCK_IN_P",
            "LOGIC_BUCK_IN_P", "CHOP_DRAIN", "CHOP_SENSE_TOP", "AON_FEED_MID", "AON_LDO_IN", "SYS_DIV_MID",
            "MOT_DIV_MID"} | {f"Q{i}_G" for i in range(1, 11)}


def drc(pcb, out, *extra):
    r = C.kicad_cli("pcb", "drc", "--severity-all", "--all-track-errors", "--format", "json", "-o", out, *extra, pcb,
                    cwd=os.path.dirname(pcb))
    return json.load(open(out)), r.returncode


def native():
    d, pcb = C.project_copy()
    res = {}
    out = os.path.join(d, "erc.json")
    C.kicad_cli("sch", "erc", "--severity-all", "--format", "json", "-o", out, os.path.join(d, "HomeMy_PMU_RevA.kicad_sch"), cwd=d)
    e = json.load(open(out))
    res["erc"] = {"kicad": e["kicad_version"], "sheets": len(e["sheets"]),
                  "violations": sum(len(s.get("violations", [])) for s in e["sheets"]),
                  "ignored_checks": [x.get("key") for x in e.get("ignored_checks", [])]}
    for name, extra in (("drc_as_saved", ["--schematic-parity"]), ("drc_refilled_zones", ["--schematic-parity", "--refill-zones"])):
        dd, _ = drc(pcb, os.path.join(d, name + ".json"), *extra)
        res[name] = {"kicad": dd["kicad_version"], "violations": len(dd["violations"]),
                     "unconnected_items": len(dd["unconnected_items"]), "schematic_parity": len(dd.get("schematic_parity", []))}
    return res


def hv():
    d, pcb = C.project_copy()
    pro_path = os.path.join(d, "HomeMy_PMU_RevA.kicad_pro")
    pro = json.load(open(pro_path))
    ns = pro["net_settings"]
    hvx = dict(next(k for k in ns["classes"] if k["name"] == "Default"), name="HVX", priority=99)
    ns["classes"].append(hvx)
    for x in sorted(HV_EXACT):
        ns["netclass_patterns"].append({"netclass": "HVX", "pattern": x})
    json.dump(pro, open(pro_path, "w"), indent=2)
    with open(os.path.join(d, "HomeMy_PMU_RevA.kicad_dru"), "a") as f:
        f.write('\n(rule "REVIEW HV to LV clearance"\n  (condition "A.hasNetclass(\'HVX\') && !B.hasNetclass(\'HVX\')")\n  (constraint clearance (min 0.6mm)))\n')
    dd, _ = drc(pcb, os.path.join(d, "hv.json"))
    rows = []
    for x in dd["violations"]:
        if x["type"] != "clearance":
            continue
        m = re.search(r"actual ([0-9.]+) mm", x["description"])
        ds = [i["description"] for i in x["items"]]
        nets = [re.search(r"\[([^\]]+)\]", s).group(1) if re.search(r"\[([^\]]+)\]", s) else "?" for s in ds]
        kinds = sorted("pad" if s.startswith("Pad") else s.split()[0].lower() for s in ds)
        inner = all(re.search(r" on In[12]\.Cu(,|$| )", s) and " - " not in s.split(" on ")[-1][:14] for s in ds)
        rows.append({"actual_mm": float(m.group(1)) if m else None, "kinds": kinds, "inner_layer_only": inner,
                     "hv_net": next((n for n in nets if n in HV_EXACT), "?"), "other_net": next((n for n in nets if n not in HV_EXACT), "?"),
                     "at": [round(x["items"][0]["pos"]["x"], 2), round(x["items"][0]["pos"]["y"], 2)], "items": ds})
    rows.sort(key=lambda r: r["actual_mm"])
    summary = collections.Counter()
    for r in rows:
        band = "<0.4" if r["actual_mm"] < 0.4 else "0.4-0.6"
        summary[f"{band} | {'pad beteiligt' if 'pad' in r['kinds'] else '+'.join(r['kinds'])} | {'nur Innenlage' if r['inner_layer_only'] else 'Aussenlage/Durchkontaktierung'}"] += 1
    return {"rule": "42-V-Netze (HVX) zu allen anderen Netzen >= 0.6 mm", "hv_nets": sorted(HV_EXACT),
            "count": len(rows), "min_mm": rows[0]["actual_mm"] if rows else None, "summary": dict(sorted(summary.items())),
            "pad_involved_below_0.4mm": [r for r in rows if "pad" in r["kinds"] and r["actual_mm"] < 0.4], "all": rows}


def power():
    import pcbnew
    d, pcb = C.project_copy()
    b = pcbnew.LoadBoard(pcb)
    mm = pcbnew.ToMM
    removed = collections.Counter()
    for t in list(b.GetTracks()):
        n = t.GetNetname()
        if n not in C.POWER_NETS:
            continue
        if t.GetClass() == "PCB_VIA":
            if mm(t.GetDrillValue()) < 0.39 or mm(t.GetWidth(pcbnew.F_Cu)) < 0.79:
                removed[n + " via<0.8/0.4"] += 1
                b.Remove(t)
        elif mm(t.GetWidth()) < 1.0:
            removed[n + " track<1.0"] += 1
            b.Remove(t)
    pcbnew.SaveBoard(pcb, b)
    dd, _ = drc(pcb, os.path.join(d, "pwr.json"))
    refs = collections.defaultdict(set)
    for x in dd["unconnected_items"]:
        for it in x["items"]:
            m = re.search(r"Pad (\S+) \[([^\]]+)\] of ([A-Z]+\d+)", it["description"])
            if m:
                refs[m.group(3)].add(f"{m.group(1)}/{m.group(2)}")
    key = lambda s: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", s)]
    return {"removed": dict(removed), "unconnected_items": len(dd["unconnected_items"]),
            "components_fed_only_through_thin_copper": {r: sorted(refs[r]) for r in sorted(refs, key=key)},
            "note": "Q1-Q10, RSH1/2-Kraftpads, J1-J6, BC1-15 und NT1-8 fehlen in dieser Liste: sie bleiben ueber Flaechen verbunden."}


if __name__ == "__main__":
    todo = sys.argv[1:] or ["native", "hv", "power"]
    os.makedirs(C.OUT, exist_ok=True)
    for name, fn, fname in (("native", native, "native_checks.json"), ("hv", hv, "hv_clearance.json"), ("power", power, "power_continuity.json")):
        if name in todo:
            r = fn()
            json.dump(r, open(os.path.join(C.OUT, fname), "w"), indent=1, ensure_ascii=False)
            print(name, json.dumps({k: v for k, v in r.items() if k not in ("all", "hv_nets", "pad_involved_below_0.4mm", "components_fed_only_through_thin_copper")}, ensure_ascii=False)[:700])
