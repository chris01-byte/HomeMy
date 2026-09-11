"""Three explicit, independently screened main/motion gate distribution trees."""
from rebuild import *
import sys
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from finish_280_routes import Controlled
import pcbnew as pcb
def main():
    guard();b=pcb.LoadBoard(str(BOARD));c=Controlled(b);F,I1,I2=pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu
    H,D,M='MAIN_HGATE','MAIN_DGATE','MOTION_GATE_DRIVE'
    parts=[(['U1.14',(67.6,84.75),(69.6,84.75)],.2,F),([(62.7,31.4125),(62.7,51.4125),(62.7,71.4125),(62.7,75.5),(76.5,75.5),(76.5,84.75),(69.6,84.75)],.2,I1)]
    vias=[(69.6,84.75)]
    for n,y in [(1,31.4125),(2,51.4125),(3,71.4125)]:parts.append(([f'R{n}.1',(62.7,y)],.2,F));vias.append((62.7,y))
    c.route('Main HGATE distribution',H,parts,[(p,.6,.3) for p in vias])
    parts=[(['U1.1',(62.5,82.75),(62.4,82.5)],.2,F),([(62.4,82.5),(62.4,80.4),(79.4,80.4),(79.4,54.4125),(79.4,34.4125),(79.4,14.4125)],.2,I2)]
    vias=[(62.4,82.5)]
    for n,y in [(4,14.4125),(5,34.4125),(6,54.4125)]:parts.append(([f'R{n}.1',(79.4,y)],.2,F));vias.append((79.4,y))
    c.route('Main DGATE distribution',D,parts,[(p,.6,.3) for p in vias])
    parts=[(['U2.14',(159.6,78.75)],.2,F),(['R34.2',(164.9125,90.1)],.2,F),
      ([(159.6,78.75),(159.6,76.5),(153,76.5),(150.4,73.9),(150.4,61.4125),(150.4,31.4125),(149.7,31.4125)],.2,I2),
      ([(150.4,61.4125),(149.7,61.4125)],.2,I2),
      ([(159.6,78.75),(167.2,71.15),(167.2,68.8),(166.4,68),(166.4,44.4125),(166.4,14.4125)],.2,I2),
      ([(159.6,78.75),(159.6,84.7875),(164.9125,90.1)],.2,I2)]
    vias=[(159.6,78.75),(164.9125,90.1)]
    for n,x,y in [(7,149.7,31.4125),(8,149.7,61.4125),(9,166.4,14.4125),(10,166.4,44.4125)]:parts.append(([f'R{n}.1',(x,y)],.2,F));vias.append((x,y))
    c.route('Motion gate distribution',M,parts,[(p,.6,.3) for p in vias])
    b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-03-gate-recipes.json',{'recipes':c.records,'pcb_sha256':sha(BOARD)})
    return b,c,f
if __name__=='__main__':owners=main()
