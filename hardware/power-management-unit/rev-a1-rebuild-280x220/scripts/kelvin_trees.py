"""Four finite, independently screened Kelvin trees; no power-class exception."""
from rebuild import *
import sys
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from finish_280_routes import Controlled
import pcbnew as pcb

def main():
    guard();b=pcb.LoadBoard(str(BOARD));c=Controlled(b);F,B,I1,I2=pcb.F_Cu,pcb.B_Cu,pcb.In1_Cu,pcb.In2_Cu
    def tree(net,contacts,branches):
        parts=[([pad,v],.2,F) for pad,v in contacts]
        parts += [(points,.2,layer) for layer,points in branches]
        c.route(net,net,parts,[(v,.6,.3) for pad,v in contacts])
    tree('MAIN_KELVIN_P',[
      ('RSH1.2',(25.975,40.6)),('R21.1',(62.7,76.5)),('R23.1',(72,81)),('R223.1',(33,18.5))],[
      (I2,[(25.975,40.6),(25.975,38),(37.5,38),(37.5,74.8),(62.7,74.8),(62.7,76.5)]),
      (I1,[(25.975,40.6),(26,40.5),(26,33.5),(26.5,33),(26.5,27.5),(27,27),(27,25.5),(32.5,20),(32.5,19),(33,18.5)]),
      (B,[(62.7,76.5),(62.5,76.5),(63,77),(63.5,77),(64,77.5),(64.5,77.5),(65,78),(65.5,78),(67,79.5),(68,79.5),(70.5,82),(71,81.5),(71.5,81.5),(72,81)]),
      (F,[(33,18.5),'TP3.1'])])
    tree('MAIN_KELVIN_N',[
      ('RSH1.3',(34.025,40.6)),('R224.1',(37,19.9)),('C5.2',(69.2,79.1))],[
      (F,['C4.2','C5.2']),
      (I1,[(34.025,40.6),(36,38.625),(36,20.9),(37,19.9)]),
      (I1,[(34.025,40.6),(36.8,40.6),(36.8,73.9),(60.5,73.9),(60.5,77.5),(66,77.5),(66.5,78),(68,78),(69,79),(69.2,79.1)]),
      (F,[(34.025,40.6),'TP4.1'])])
    tree('MOTION_KELVIN_P',[
      ('RSH2.2',(107.975,40.6)),('R30.1',(167.1,78.9125)),('R32.1',(167.1,72.9125))],[
      (I1,[(107.975,40.6),(107.975,38),(121.5,38),(121.5,66),(168,66),(168,72.9125),(168,78.9125),(167.1,78.9125)]),
      (I1,[(168,72.9125),(167.1,72.9125)]),
      (F,[(167.1,72.9125),(168.1875,74),'TP7.1'])])
    tree('MOTION_KELVIN_N',[
      ('RSH2.3',(116.025,40.6)),('C12.2',(163.9,73.3))],[
      (F,[(160.4,78.45),'C11.2',(162.95,76.5),'C12.2']),
      (I1,[(116.025,40.6),(120.8,40.6),(120.8,66.7),(160.5,66.7),(160.5,66.5),(161,67),(161,67.5),(161.5,68),(161.5,68.5),(162,69),(162,70.5),(160,72.5),(160,73),(160.5,73.5),(164,73.5),(163.9,73.3)]),
      (F,[(116.025,40.6),'TP8.1'])])
    b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-04-kelvin-recipes.json',{'recipes':c.records,'pcb_sha256':sha(BOARD),'review_scope':'Native pad/track/via/keepout screening; no electromagnetic coupling or transient qualification inferred.'})
    return b,c,f
if __name__=='__main__':owners=main()
