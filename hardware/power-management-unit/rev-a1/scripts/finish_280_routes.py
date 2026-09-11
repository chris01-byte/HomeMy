"""Explicit, finite routing recipes for the lead's fixed-size completion task.

These helpers never search globally or weaken a rule. Each whole proposal is
screened against native shapes and existing keepouts, then validated after fill.
"""
from collections import Counter
import math
import pcbnew as pcb
from bounded_seed import Screen,LAYERS
from bounded_geometry import point,xy
from finish_280 import BOARD,OUT,read,guard,action,attempt,sha,write
from finish_280_cad import refill

class Controlled:
    def __init__(self,board):
        self.board=board;self.screen=Screen(board);self.owners=[];self.records=[]
        self.pads={f.GetReference()+'.'+p.GetNumber():p for f in board.GetFootprints() for p in f.Pads()}
    def loc(self,p):return xy(self.pads[p].GetPosition()) if isinstance(p,str) else p
    def segment(self,net,a,b,w,l):
        t=pcb.PCB_TRACK(self.board);t.SetNet(self.board.FindNet(net));t.SetStart(point(*self.loc(a)));t.SetEnd(point(*self.loc(b)))
        t.SetWidth(pcb.FromMM(w));t.SetLayer(l);t.SetLocked(True);self.owners.append(t);return t
    def via(self,net,p,d=.6,h=.3):
        v=pcb.PCB_VIA(self.board);v.SetNet(self.board.FindNet(net));v.SetPosition(point(*self.loc(p)))
        v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetWidth(pcb.FromMM(d));v.SetDrill(pcb.FromMM(h));v.SetLocked(True)
        self.owners.append(v);return v
    def obstacles(self,t):
        reason=self.screen.reason(t)
        if not reason:return []
        box=t.GetBoundingBox();box.Inflate(pcb.FromMM(.201));hits={}
        for l in LAYERS:
            if not t.IsOnLayer(l):continue
            shape=t.GetEffectiveShape(l)
            for i,j in self.screen.cells(box):
                for o in self.screen.grid[i,j,l]:
                    uid=o.m_Uuid.AsString()
                    if uid in hits or o.GetNetname()==t.GetNetname():continue
                    if shape.Collide(self.screen.shapes[id(o),l],pcb.FromMM(.2)-10):
                        hits[uid]={'uuid':uid,'net':o.GetNetname(),'kind':'pad' if isinstance(o,pcb.PAD) else 'via' if isinstance(o,pcb.PCB_VIA) else 'track',
                                   'xy':xy(o.GetPosition()),'layer':self.board.GetLayerName(l),'locked':o.IsLocked(),
                                   'pad':o.GetParentFootprint().GetReference()+'.'+o.GetNumber() if isinstance(o,pcb.PAD) else None}
        return list(hits.values()) or [{'reason':reason}]
    def route(self,label,net,parts,vias=(),apply=True):
        proposed=[self.segment(net,a,b,w,l) for pts,w,l in parts for a,b in zip(pts,pts[1:]) if math.dist(self.loc(a),self.loc(b))>1e-7]
        proposed += [self.via(net,p,d,h) for p,d,h in vias]
        bad=[{'item':i,'obstacles':self.obstacles(t)} for i,t in enumerate(proposed) if self.screen.reason(t)]
        record={'label':label,'net':net,'adopted':not bad and apply,'blocked':bad,
                'parts':[{'points_mm':[self.loc(p) for p in pts],'width_mm':w,'layer':self.board.GetLayerName(l)} for pts,w,l in parts],
                'vias':[{'xy_mm':p,'diameter_mm':d,'drill_mm':h} for p,d,h in vias]}
        if not bad and apply:
            for t in proposed:self.board.Add(t);self.screen.index(t)
            record['added_uuids']=[t.m_Uuid.AsString() for t in proposed]
        self.records.append(record);print(label,'adopted' if record['adopted'] else 'blocked' if bad else 'screen clear',len(bad),flush=True)
        return not bad
    def finish(self,label):
        guard(read());filler=refill(self.board)
        action(label,self.records);write(OUT/(label+'-recipes.json'),{'pcb_sha256':sha(BOARD),'recipes':self.records})
        return filler
