"""Final finite high-driver escape and controlled chopper sense/gate branches."""
from rebuild import *
import sys
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from finish_280_routes import Controlled
import pcbnew as pcb
def main():
    guard();b=pcb.LoadBoard(str(BOARD));c=Controlled(b);F,I1,I2=pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu
    c.route('Final bounded chopper high-drive escape','CHOP_DRIVE_H',[
      (['U33.2',(225.1,49)],.2,F),([(225.1,49),(226,49),(226,45.9),(228.5875,45.9)],.2,I2),
      ([(228.5875,45.9),'R319.1'],.2,F)],[(p,.6,.3) for p in [(225.1,49),(228.5875,45.9)]])
    c.route('Chopper gate controlled sense/discharge branches','CHOP_GATE',[
      ([(232,49.6),(232,50.8)],.2,F),(['R305.1',(210,99)],.2,F),(['Q42.1',(215.7,131.05)],.2,F),
      ([(234.75,43.8),(236,42.55),'TP26.1'],.2,F),
      ([(232,50.8),(230.5,53.5),(230.5,66),(219,77.5),(219,79.5),(210,99)],.2,I2),
      ([(210,99),(210,106.5),(209,107.5),(209,112.5),(210.5,114),(210.5,119.5),(211,120),(211.5,120),(212,120.5),(212,126),(215.7,131.05)],.2,I2)
      ],[(p,.6,.3) for p in [(232,50.8),(210,99),(215.7,131.05)]])
    c.route('Chopper controlled measurement tree','CHOP_SENSE',[
      (['R331.2',(187,95)],.2,F),(['R304.1',(182,106)],.2,F),(['C305.1',(179.2,107)],.2,F),(['U32.5',(175.8,112.65)],.2,F),
      ([(187,95),(184,101.5),(184,103),(182.5,104.5),(182.5,105.5),(182,106)],.2,I1),
      ([(182,106),(181,106),(180.5,106.5),(179.5,106.5),(179.2,107)],.2,I1),
      ([(179.2,107),(178.5,107.5),(178.5,108.5),(177,110),(177,110.5),(176.5,111),(176.5,112),(175.8,112.65)],.2,I1),
      (['R304.1',(182,105),(183,105),(183.5,105.5),(185.5,105.5),(186,106),(187,106),'R303.2'],.2,F)
      ],[(p,.6,.3) for p in [(187,95),(182,106),(179.2,107),(175.8,112.65)]])
    b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-05-chopper-recipes.json',{'pcb_sha256':sha(BOARD),'recipes':c.records,
      'limitations':['The U33/resistor/Q40 drive loop is local. The gate feedback branch to R305 remains55.33mm with35.21mm further Q42 branch.','Native geometric connectivity does not qualify transient behavior or coupling.']})
    return b,c,f
if __name__=='__main__':owners=main()
