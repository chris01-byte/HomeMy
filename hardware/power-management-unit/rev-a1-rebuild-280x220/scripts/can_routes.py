"""Finite CAN pair trees retaining the original split termination."""
from rebuild import *
import sys
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from finish_280_routes import Controlled
import pcbnew as pcb
def main():
    guard();b=pcb.LoadBoard(str(BOARD));c=Controlled(b);F,B=pcb.F_Cu,pcb.B_Cu
    for net,contacts,branches in [
      ('CAN_H',[('J16.1',(33.125,216.5)),('J17.1',(48.125,216.5)),('U13.7',(47.1,200.365)),('D40.1',(24.05,203.1)),('R243.1',(27.2,197))],[
        [(24.05,203.1),(24.05,198.3),(27.2,198.3),(47.1,198.3),(47.1,200.365)],[(27.2,197),(27.2,198.3)],
        [(24.05,203.1),(24.95,204),(24.95,216.5),(33.125,216.5),(48.125,216.5)]]),
      ('CAN_L',[('J16.2',(34.375,215.7)),('J17.2',(49.375,215.7)),('U13.6',(47.1,201.635)),('D40.2',(25.95,203.1)),('R244.2',(32.8,205))],[
        [(25.95,203.1),(25,202.15),(25,199.1),(46.3,199.1),(46.3,200.835),(47.1,201.635)],
        [(25.95,203.1),(25.95,205),(25.95,215.7),(34.375,215.7),(49.375,215.7)],[(25.95,205),(32.8,205)]])]:
        c.route(net+' controlled tree',net,[([pad,v],.25,F) for pad,v in contacts]+[(points,.25,B) for points in branches],[(v,.6,.3) for pad,v in contacts])
    c.route('Local AON regulator input','AON_LDO_IN',[(['C200.1','U15.1'],.4,F)])
    b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-05-can-recipes.json',{'pcb_sha256':sha(BOARD),'recipes':c.records,'limitations':'Paired geometric routing, not a controlled-impedance or EMC qualification; existing split termination unchanged.'})
    return b,c,f
if __name__=='__main__':owners=main()
