"""Last bounded local reference tree and partial10V distribution, independently reviewed."""
from rebuild import *
import sys
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from finish_280_routes import Controlled
import pcbnew as pcb

def main():
    guard();b=pcb.LoadBoard(str(BOARD));before=sha(BOARD);c=Controlled(b);F,B,I2=pcb.F_Cu,pcb.B_Cu,pcb.In2_Cu
    supply_contacts=[('U33.1',(226.1,51)),('C308.1',(196.3,89)),('R318.1',(210.2,89)),('C309.1',(210,87)),('R310.1',(172.2,107)),('R307.1',(174.9,104.9125)),('C302.1',(198.3,103)),('C304.1',(178.3,120)),('R316.1',(176.9,123.9125)),('C301.1',(202.5,105)),('U31.2',(201.1,109.2)),('U30.1',(207.5,110.025)),('TP27.1',(203.4,114.1)),('Q43.2',(196.0625,138.9)),('R330.1',(205.2,152))]
    supply_branches=[[(204,85),(204,154)],[(226.1,51),(219,51),(219,85),(204,85)],[(196.3,89),(196.3,90.2),(204,90.2)],[(210.2,89),(204,89)],[(210,87),(204,87)],[(172.2,107),(172.2,101.6),(177.2,101.6),(204,101.6)],[(174.9,104.9125),(174.9,101.6)],[(198.3,103),(198.3,101.6)],[(177.2,101.6),(177.2,120),(177.2,123.9125),(176.9,123.9125)],[(178.3,120),(177.2,120)],[(202.5,105),(204,105)],[(201.1,109.2),(204,109.2)],[(207.5,110.025),(204,110.025)],[(203.4,114.1),(204,114.1)],[(196.0625,138.9),(204,138.9)],[(205.2,152),(204,152)]]
    supply_parts=[([pad,v],.2,F) for pad,v in supply_contacts]+[(pts,.6,B) for pts in supply_branches]
    proposed=[c.segment('CHOP_10V',a,d,w,l) for pts,w,l in supply_parts for a,d in zip(pts,pts[1:])]+[c.via('CHOP_10V',v,.6,.3) for pad,v in supply_contacts]
    source=pcb.LoadBoard(str(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'));original={t.m_Uuid.AsString() for t in source.GetTracks()}
    hits={o['uuid']:o for t in proposed for o in c.obstacles(t) if 'uuid' in o};items={t.m_Uuid.AsString():t for t in b.GetTracks()};removed=[];held=[]
    for uid,o in hits.items():
        t=items.get(uid)
        if o['net']=='BATT_N' and isinstance(t,pcb.PCB_VIA) and not t.GetParentGroup() and uid not in original:
            b.Remove(t);held.append(t);removed.append({'uuid':uid,'xy_mm':o['xy']})
    c=Controlled(b)
    ref_contacts=[('U31.6',(196.1,107.365)),('C303.1',(201,108)),('TP28.1',(191,108.4)),('R312.1',(186,121)),('R314.1',(189.1,118.9125)),('U32.4',(175.3,112)),('U32.7',(175.8,113.95)),('C311.1',(214.2,145)),('R311.1',(209.9,148)),('R325.1',(220,143)),('U36.6',(222.3,148.05)),('U36.3',(218.1,151.1))]
    ref_branches=[
      [(196.1,107.365),(191,108.4)],
      [(196.1,107.365),(196,107.5),(196,106),(196.5,105.5),(197,105.5),(198.5,107),(199,107),(199.5,107.5),(200.5,107.5),(201,108)],
      [(191,108.4),(191,108.5),(190.5,108.5),(189.5,109.5),(189.5,110)],
      [(189.5,110),(189.5,115.5),(189,116),(189,119),(189.1,118.9125)],
      [(189,119),(188.5,119.5),(188,119.5),(187,120.5),(186.5,120.5),(186,121)],
      [(189.5,110),(189,110.5),(178.5,110.5),(178,111),(177.5,111),(177,111.5),(176.5,111.5),(176,112),(175.3,112)],
      [(176,112),(176.5,112.5),(176.5,113.5),(176,114),(175.8,113.95)],
      [(201,108),(202,108),(202,110.5),(202.5,111),(202.5,129.5),(209,136),(209,137),(211.5,139.5),(211.5,140),(212,140.5),(212,141),(212.5,141.5),(212.5,142),(213,142.5),(213,143),(213.5,143.5),(213.5,144.5),(214,145),(214.2,145)],
      [(214.2,145),(209.9,148)],[(214.2,145),(215.5,145),(217,143.5),(219.5,143.5),(220,143)],
      [(220,143),(220,144),(221.5,145.5),(221.5,146),(222,146.5),(222,147.5),(222.5,148),(222.3,148.05)],
      [(222.5,148),(222,148.5),(221.5,148.5),(219.5,150.5),(218.5,150.5),(218,151),(218.1,151.1)]]
    c.route('Chopper reference tree','CHOP_REF2V5',[([pad,v],.2,F) for pad,v in ref_contacts]+[(pts,.2,I2) for pts in ref_branches]+[(['R327.1',(212,152),(214.5,152),(215.5,151),(218,151),(218.1,151.1)],.2,F)],[(v,.6,.3) for pad,v in ref_contacts])
    c.route('Chopper 10V partial supply tree','CHOP_10V',supply_parts,[(v,.6,.3) for pad,v in supply_contacts])
    if not all(r['adopted'] for r in c.records):
        write(OUT/'cycle-06-chopper-rejected.json',{'pcb_sha256':before,'saved':False,'recipes':c.records,'proposed_return_via_removal':removed});print('Atomic chopper proposal rejected; board unchanged',flush=True);return b,c,source,held
    b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-06-chopper-recipes.json',{'input_sha256':before,'pcb_sha256':sha(BOARD),'recipes':c.records,'retired_only_new_BATT_N_vias':removed,'explicit_unresolved_10V_pads':['U32.3','R323.1','R300.1','D64.2'],'limitations':'Four local 10V fanouts remain blocked after bounded virtual attempts; no further search on those roots. Reference traces stay within the CHOP_GND outline but actual filled return paths/EMC remain to verify.'})
    print('Chopper reference complete; 15-pad10V tree adopted; retired',len(removed),'new return vias',flush=True)
    return b,c,source,f,held
if __name__=='__main__':owners=main()
