#!/usr/bin/python

import urjtag

# Class jtag_bus provide the real communication with the controller
# The constructor accepts: name of the cable, name of the part,
# number of the part in the chain (in the case if we have two or more
# identical chips in the chain), width of the address bus
# and width of the data bus.
class jtag_bus:
   def __init__(self,cable,partid,index,a_width,d_width):
     self.u=urjtag.chain()
     self.u.cable(cable)
     #u.cable("DLC5 ppdev /dev/parport0")
     self.u.tap_detect()
     self.m_width=max(a_width,d_width)
     self.mask=(1<<self.m_width)-1
     #Now we find the part we want to control
     for i in range(0,self.u.len()):
        self.u.part(i)
        if self.u.partid(i)== partid and index==1: 
           self.u.add_register("BAR",self.m_width+2)
           self.u.add_instruction("BUSACC","000010","BAR")
           self.u.set_instruction("BUSACC")
           self.u.shift_ir()
           self.part_nr = i
        else:
           self.u.set_instruction("BYPASS")
           self.u.shift_ir()
        if self.u.partid(i)==partid:
           index -= 1
   def jt_write(self,address,data):
       self.u.set_dr_in((3 << self.m_width) | (address & self.mask))
       self.u.shift_dr()
       self.u.set_dr_in(data & self.mask)
       self.u.shift_dr()
   def jt_read(self,address):
       self.u.set_dr_in((2 << self.m_width) | (address & self.mask))
       self.u.shift_dr()
       self.u.set_dr_in(0)
       self.u.shift_dr()
       return self.u.get_dr_out()



