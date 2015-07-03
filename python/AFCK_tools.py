# This is a PUBLIC DOMAIN code written by Wojciech M. Zabolotny (wzab@ise.pw.edu.pl)
from jtag_bus import *
from i2c_tools import *
from i2c_obj import *
from Si57x import *
from ADN4604 import *
from FM_S14 import *
import urjtag
import time
#First set the SCANSTA and configure I2C controller
#as the configuration is long, I've added a way
#to disable itm, when you know, that the board
#is already configured
reconfigure = True
#reconfigure = False
if reconfigure:
  t1=time.time()
  u=urjtag.chain()
  u.cable("xpc_ext")
  u.set_frequency(6000000)
  u.addpart(8)
  u.run_svf("st111.svf")
  u.tap_detect()
  print "Next operation may take even 15 minutes. Don't interrupt it, ot the XPC programmer may hang"
  u.run_svf("AFCK_i2c_bscan_ctrl.svf")
  u.disconnect()
  t2=time.time()
  print "Initialization time:" + str(t2-t1)
  del(u)
#If we got here, it means, that SCANSTA111 got configured
#and I2C_BSCAN controller is loaded into FPGA

#build the controller interface object
#How we can find the partid for our chip???
jb=jtag_bus("xpc_ext",0x43651093,1,4,32)
#Create the I2C controller object
i2c=i2c_ctrl(jb, 8)
#Start the I2C controller
jb.jt_write(5, 0)
jb.jt_write(5, 1)
jb.jt_write(5, 3)
i2c.start()
#Create the I2C root switch
r1=i2c_root(srv=i2c)
class i2c_bus_switch(i2c_root_switch):
   # __init__ is inherited from i2c_root_switch
   def sel_branch(self, branch_num):
       jb.jt_write(4, branch_num)
rs1=i2c_bus_switch(branch=(r1, None))
#Create I2C busses
b_f1c0=(rs1, 0)  #FMC1 clock 0
b_f1c1=(rs1, 1)  #FMC1 clock 1
b_f2c0=(rs1, 2)  #FMC2 clock 0
b_f2c1=(rs1, 3)  # FMC2 clock 1
b_main=(rs1, 4) # Main bus on AFCK
#Create I2C switch on main bus
s_main= i2c_pca9547bs(branch=b_main, address=112)
#Create I2C branches after the switch
b_si57x=(s_main, 2)
b_adn=(s_main, 4)
#Create chip objects
c_si57x=i2c_Si57x(branch=b_si57x,  address=0x55)
c_adn=i2c_ADN4604(branch=b_adn, address=75)
c_f1c0=i2c_FMS14Q(branch=b_f1c0,  address=110)    
c_f1c1=i2c_FMS14Q(branch=b_f1c1,  address=110)    
c_f2c0=i2c_FMS14Q(branch=b_f2c0,  address=110)    
c_f2c1=i2c_FMS14Q(branch=b_f2c1,  address=110)

#The procedure below connects given input to output
#in the clock matrix n_in = -1 switches off the output
    
def ClkMtx_set_out(n_in,  n_out): 
    n_in = int(n_in)
    n_out = int(n_out)
    if (n_in < -1) | (n_in > 15) :
        raise Exception("wrong n_in:%d (must be between -1 and 15)" % n_in)
    if (n_out < 0) | (n_out > 15):
        raise Exception("wrong n_out:%d (must be between 0 and 15)" % n_out)
    if n_in==-1:
        # Switch off that output
        c_adn.write(0x20+n_out,  (0x00, ))
    else:
        # Select the input and switch on the output
        # Number of register is 0x90+n_out/2
        nr_reg = 0x90+int(n_out/2)
        # Nibble in the register is n_out % 2
        if n_out % 2 == 1:
            mask = 0x0f
            val =  n_in*16
        else:
            mask = 0xf0
            val = n_in
    #Program the switch matrix
    old_val =c_adn.read(nr_reg)
    c_adn.write(nr_reg,   (old_val & mask ) | val )
    # Trigger matrix update
    c_adn.write(0x81, 0x00)
    c_adn.write(0x80, 0x01)
    # Switch on the output
    c_adn.write(0x20+n_out,  0x30)
    
#Procedure for setting of Si57x clock (with switching I2C Muxes)
def SiSetFrq(frq):
  c_si57x.set_frq(frq)

#Procedure for setting of FMC clock
def FmcSetFrq(fmc, clk,  frq):
  if (fmc==1) & (clk==0):
    c=c_f1c0
  elif (fmc==1) & (clk==1):
    c=c_f1c1
  elif (fmc==2) & (clk==0):
    c=c_f2c0
  elif (fmc==2) & (clk==1):
    c=c_f2c1
  else:
    raise Exception("Incorrect FMC number: %g (should be 1 or 2 ) or clock number: %g (should be 0 or 1)" % (fmc,  clk))
  c.set_frq(frq)
  
