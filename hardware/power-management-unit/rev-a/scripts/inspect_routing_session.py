"""Snapshot a router session and import it into an isolated native board copy."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import traceback
import pcbnew as pcb
from build_board import force_exit
from sync_nc_nets import sync_nc_nets

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--session',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,required=True)
    ap.add_argument('--board',type=Path,default=ROOT/'kicad/HomeMy_PMU_RevA.kicad_pcb');a=ap.parse_args()
    source=a.board.resolve();out=a.output_dir.resolve()
    if out==source.parent or out in source.parents:raise ValueError('Output must be an isolated directory')
    out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Use a new isolated inspection directory')
    before=sha(source)
    session=a.session.read_bytes();session_hash=hashlib.sha256(session).hexdigest()
    if session_hash!=sha(a.session):raise ValueError('Router session changed during snapshot; retry in a new directory')
    frozen=out/'frozen.ses';frozen.write_bytes(session)
    target=out/source.name
    shutil.copy2(source,target)
    for suffix in ['.kicad_pro','.kicad_dru']:
        p=source.with_suffix(suffix)
        if p.exists():shutil.copy2(p,target.with_suffix(suffix))
    table=source.parent/'fp-lib-table'
    if table.exists():
        (out/table.name).write_text(table.read_text(encoding='utf-8').replace('${KIPRJMOD}',source.parent.as_posix()),encoding='utf-8')
    board=pcb.LoadBoard(str(target))
    if not pcb.ImportSpecctraSES(board,str(frozen)):raise ValueError('Native session import failed')
    sync=sync_nc_nets(board)
    board.BuildConnectivity();filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones())
    pcb.SaveBoard(str(target),board)
    if before!=sha(source):raise ValueError('Main PCB changed during isolated inspection; report snapshot only')
    result=dict(metadata=dict(rev_a_engineering_prototype=True,rev_b_production=False,
                    state='isolated_router_diagnostic_not_order_release',checked_at_utc=datetime.now(timezone.utc).isoformat(),main_pcb_written=False),
                main_pcb=str(source),main_pcb_sha256=before,session_source=str(a.session.resolve()),
                frozen_session_sha256=session_hash,temporary_board=str(target),temporary_board_sha256=sha(target),nc_sync=sync,
                footprint_count=len(list(board.GetFootprints())),track_via_count=len(list(board.GetTracks())))
    (out/'inspection-manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['main_pcb_sha256','frozen_session_sha256','temporary_board','track_via_count']}),flush=True)
    return board,filler


if __name__=='__main__':
    try:owners=main()
    except BaseException:traceback.print_exc();force_exit(1)
    force_exit(0)
