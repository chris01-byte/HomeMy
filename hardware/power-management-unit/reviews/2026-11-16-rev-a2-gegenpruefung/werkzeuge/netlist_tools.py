#!/usr/bin/env python3
"""Netzliste des A2-Schaltplans exportieren und als kompakte Texte je Schaltplanblatt ablegen.

Aufruf: python3 netlist_tools.py            -> daten/netzliste/<blatt>.txt und daten/netzliste/nets.txt
Als Modul: comps, nets, pins = load(pfad)   (pins[ref][pin] = (netz, pinfunktion, pintyp))
"""
import collections, contextlib, io, os, re, sys
import xml.etree.ElementTree as ET
import _common as C


def load(path=None):
    path = path or C.export_netlist()
    t = ET.parse(path).getroot()
    comps = {}
    for c in t.find("components"):
        d = {"ref": c.get("ref"), "value": c.findtext("value"), "footprint": c.findtext("footprint"),
             "fields": {}, "props": {}, "sheet": None}
        f = c.find("fields")
        if f is not None:
            for x in f:
                d["fields"][x.get("name")] = x.text
        for p in c.findall("property"):
            d["props"][p.get("name")] = p.get("value")
        sp = c.find("sheetpath")
        if sp is not None:
            d["sheet"] = sp.get("names")
        d["dnp"] = "dnp" in d["props"]
        comps[d["ref"]] = d
    nets = {}
    pins = collections.defaultdict(dict)
    for n in t.find("nets"):
        L = []
        for nd in n.findall("node"):
            L.append((nd.get("ref"), nd.get("pin"), nd.get("pinfunction"), nd.get("pintype")))
            pins[nd.get("ref")][nd.get("pin")] = (n.get("name"), nd.get("pinfunction"), nd.get("pintype"))
        nets[n.get("name")] = L
    return comps, nets, pins


def natkey(s):
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", s)]


def show_ic(ref, comps, nets, pins, maxo=8):
    c = comps[ref]
    print(f"== {ref} {c['value'][:40]} [{c['footprint'].split(':')[-1][:30]}] mpn={c['fields'].get('MPN') or ''}{' DNP' if c['dnp'] else ''}")
    bynet = collections.OrderedDict()
    for p in sorted(pins[ref], key=natkey):
        net, fn, _ = pins[ref][p]
        bynet.setdefault(net, []).append((p, fn))
    for net, pl in bynet.items():
        others = sorted({r for r, _, _, _ in nets[net] if r != ref}, key=natkey)
        o = " ".join(others[:maxo]) + (f" ..(+{len(others) - maxo})" if len(others) > maxo else "")
        if len(pl) > 2:
            ps = f"{pl[0][0]}..{pl[-1][0]}({len(pl)}p) {re.sub(r'_?[0-9]+$', '', str(pl[0][1]))}"
        else:
            ps = ",".join(f"{p}:{fn}" for p, fn in pl)
        print(f"  {ps:<30} {'NC' if net.startswith('unconnected-') else net:<24} | {o}")


def show_sheet(sheet, comps, nets, pins, skip_prefix=("TP",)):
    refs = sorted([r for r, c in comps.items() if c["sheet"] == sheet], key=natkey)
    for r in refs:
        c = comps[r]
        if r.startswith(skip_prefix) or len(pins[r]) > 3:
            continue
        pn = " | ".join(f"{p}={pins[r][p][0]}" for p in sorted(pins[r], key=natkey))
        print(f"{r:<6}{c['value'][:26]:<27}{(c['fields'].get('MPN') or '')[:22]:<23}{'DNP ' if c['dnp'] else ''}{pn}")
    for r in refs:
        if len(pins[r]) > 3 and not r.startswith(skip_prefix):
            show_ic(r, comps, nets, pins)


def ground_bridges(comps, nets):
    """Bauteile, die zwei Massenetze verbinden (zeigt u. a. die einzige LOGIC_GND-BATT_N-Bruecke NT9)."""
    import itertools
    gnds = ["BATT_N", "LOGIC_GND", "LOGIC_5V_N", "CHOP_GND", "CHOPPER_N", "PC_N", "LOGIC_BUCK_N",
            "DRIVE_N", "LIFT_N", "ARM_L_N", "ARM_R_N", "CHASSIS", "LIFT_24V_N"]
    cn = collections.defaultdict(set)
    for net, nodes in nets.items():
        for r, _, _, _ in nodes:
            cn[r].add(net)
    out = []
    for a, b in itertools.combinations(gnds, 2):
        refs = sorted([r for r, s in cn.items() if a in s and b in s], key=natkey)
        if refs:
            out.append((a, b, refs))
    return out


if __name__ == "__main__":
    comps, nets, pins = load(sys.argv[1] if len(sys.argv) > 1 else None)
    out = os.path.join(C.OUT, "netzliste")
    os.makedirs(out, exist_ok=True)
    for sh in sorted({c["sheet"] for c in comps.values()}):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            show_sheet(sh, comps, nets, pins)
        open(os.path.join(out, sh.strip("/").replace("/", "_") + ".txt"), "w").write(buf.getvalue())
    with open(os.path.join(out, "nets.txt"), "w") as f:
        for name in sorted(nets):
            f.write(name + ": " + " ".join(f"{r}.{q}({fn})" for r, q, fn, _ in sorted(nets[name], key=lambda t: natkey(t[0]))) + "\n")
    with open(os.path.join(out, "massebruecken.txt"), "w") as f:
        for a, b, refs in ground_bridges(comps, nets):
            f.write(f"{a} <-> {b}: {', '.join(refs)}\n")
    print(len(comps), "Bauteile,", len(nets), "Netze ->", out)
