"""Two finite front-layer escapes around lower gate-pad banks."""
from rebuild import *
import sys
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from finish_280_routes import Controlled
import pcbnew as pcb

def main():
    guard();b=pcb.LoadBoard(str(BOARD));c=Controlled(b)
    c.route('Q4 local gate','Q4_G',[(['R4.2',(80.5,12.5875),(80.5,17),'Q4.1'],.2,pcb.F_Cu)])
    c.route('Q9 local gate','Q9_G',[(['R9.2',(167.5,12.5875),(167.5,17),'Q9.1'],.2,pcb.F_Cu)])
    b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-03-fet-gate-recipes.json',{'recipes':c.records,'pcb_sha256':sha(BOARD)})
    return b,c,f
if __name__=='__main__':owners=main()
