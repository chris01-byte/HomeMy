"""Preserve native KiCad singleton NC net names from an authoritative XML export.

The module function modifies only the supplied in-memory board. The CLI defaults
to dry-run; --apply explicitly saves a board. It never creates a name from a
guess or suppresses a DRC warning. All validation completes before any assignment.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import xml.etree.ElementTree as ET
import pcbnew as pcb

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_NETLIST=ROOT/'evidence/netlist-after-schematic-readability.xml'
DEFAULT_PARTS=ROOT/'design/assembled-parts.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_nc_nets(board, components=None, netlist_path=None, dry_run=False):
    """Assign exact XML names only to source-null, marked singleton NC pins.

    components is the normalized assembled list used by build_board, or None to
    read assembled-parts.json. Caller controls connectivity rebuild/fill/save.
    Returns a serializable plan/results record. Rejects missing/stale/ambiguous
    XML, absent physical pins, conflicting assigned nets, and routed NC copper.
    """
    netlist_path=Path(netlist_path or DEFAULT_NETLIST).resolve()
    initial_xml_hash=sha(netlist_path)
    if components is None:
        components=json.loads(DEFAULT_PARTS.read_text(encoding='utf-8'))['components']
    source={c['ref']:c for c in components}
    if len(source)!=len(components):
        raise ValueError('Duplicate source references')
    expected={(ref,str(pin)) for ref,c in source.items() if c.get('on_board',True)
              for pin,net in c['pins'].items() if net is None}
    mapping={}
    net_members={}
    tree=ET.parse(netlist_path).getroot()
    for net in tree.findall('./nets/net'):
        name=net.get('name','')
        nodes=net.findall('node')
        net_members[name]=[(n.get('ref'),n.get('pin')) for n in nodes]
        for node in nodes:
            key=(node.get('ref'),node.get('pin'))
            if key not in expected:
                if name.startswith('unconnected-') and 'no_connect' in node.get('pintype','').split('+'):
                    raise ValueError(f'XML NC pin {key} is not null in the assembled source')
                continue
            if key in mapping:
                raise ValueError(f'NC pin appears more than once in XML: {key}')
            if len(nodes)!=1 or not name.startswith('unconnected-(') or 'no_connect' not in node.get('pintype','').split('+'):
                raise ValueError(f'{key}: XML NC must be explicitly marked and alone on its unconnected net')
            mapping[key]=name
    if set(mapping)!=expected:
        raise ValueError('NC source/XML coverage mismatch: '+str(sorted(expected^set(mapping))))
    if len(set(mapping.values()))!=len(mapping):
        raise ValueError('Two intended NC pins share an XML net name')
    footprints={}
    all_pads=[]
    for fp in board.GetFootprints():
        ref=fp.GetReference()
        if ref in footprints:
            raise ValueError('Duplicate board reference '+ref)
        footprints[ref]=fp
        all_pads.extend((ref,pad) for pad in fp.Pads())
    plan=[]
    targets=set(mapping.values())
    for key,target in sorted(mapping.items()):
        ref,pin=key
        if ref not in footprints:
            raise ValueError(f'NC source component missing from board: {ref}')
        pads=[pad for pad in footprints[ref].Pads() if pad.GetNumber()==pin]
        if not pads:
            raise ValueError(f'NC source pin missing from footprint: {ref}.{pin}')
        for pad in pads:
            current=pad.GetNetname()
            if current not in ('',target):
                raise ValueError(f'{ref}.{pin}: refuses to replace assigned net {current!r} with NC {target!r}')
            plan.append((pad,dict(ref=ref,pin=pin,from_net=current,to_net=target,changed=current!=target)))
    for ref,pad in all_pads:
        name=pad.GetNetname()
        if name in targets and mapping.get((ref,pad.GetNumber()))!=name:
            raise ValueError(f'NC target net {name!r} is also used by unintended pad {ref}.{pad.GetNumber()}')
    for item in list(board.GetTracks())+list(board.Zones()):
        if item.GetNetname() in targets:
            raise ValueError('Intentional NC net already has routed copper or a zone: '+item.GetNetname())
    if sha(netlist_path)!=initial_xml_hash:
        raise ValueError('XML changed while preparing NC assignment')
    added=[]
    if not dry_run:
        for name in sorted(targets):
            if board.FindNet(name) is None:
                board.Add(pcb.NETINFO_ITEM(board,name))
                added.append(name)
        for pad,item in plan:
            if item['changed']:
                pad.SetNet(board.FindNet(item['to_net']))
    return dict(rev_a_engineering_prototype=True,rev_b_production=False,
        state='engineering_singleton_nc_net_identity_sync',dry_run=dry_run,
        netlist_path=str(netlist_path),netlist_sha256=initial_xml_hash,
        source_null_pin_count=len(expected),singleton_nc_net_count=len(mapping),
        physical_pad_instances=len(plan),pads_requiring_assignment=sum(item['changed'] for _,item in plan),
        nets_added=added,assignments=[item for _,item in plan],
        validation='Each XML net has exactly one node, source pin is null, physical pad exists, and no other pad/route/zone uses the target net',
        erc_or_drc_claim=False)


def force_exit(code):
    sys.stdout.flush()
    sys.stderr.flush()
    if os.name=='nt':
        kernel=ctypes.windll.kernel32
        kernel.GetCurrentProcess.restype=ctypes.c_void_p
        kernel.TerminateProcess.argtypes=[ctypes.c_void_p,ctypes.c_uint]
        kernel.TerminateProcess(kernel.GetCurrentProcess(),code)
    raise SystemExit(code)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board',type=Path,default=ROOT/'kicad/HomeMy_PMU_RevA.kicad_pcb')
    ap.add_argument('--netlist',type=Path,default=DEFAULT_NETLIST)
    ap.add_argument('--parts',type=Path,default=DEFAULT_PARTS)
    ap.add_argument('--report',type=Path,default=ROOT/'reports/nc-net-sync-plan.json')
    ap.add_argument('--apply',action='store_true')
    args=ap.parse_args()
    before=sha(args.board)
    parts=json.loads(args.parts.read_text(encoding='utf-8'))['components']
    board=pcb.LoadBoard(str(args.board.resolve()))
    result=sync_nc_nets(board,parts,args.netlist,dry_run=not args.apply)
    if args.apply:
        board.BuildConnectivity()
        if not pcb.SaveBoard(str(args.board.resolve()),board):
            raise RuntimeError('Native board save failed')
    result.update(board_sha256_before=before,board_sha256_after=sha(args.board),
        source_parts_sha256=sha(args.parts),board_saved=bool(args.apply))
    if not args.apply and result['board_sha256_before']!=result['board_sha256_after']:
        raise RuntimeError('Input board changed during dry-run; repeat after other edits finish')
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'Validated {result["singleton_nc_net_count"]} singleton NC nets; '
          f'{result["pads_requiring_assignment"]} pads require naming; board saved={args.apply}')


if __name__=='__main__':
    try:
        main()
    except BaseException:
        traceback.print_exc()
        force_exit(1)
    force_exit(0)
