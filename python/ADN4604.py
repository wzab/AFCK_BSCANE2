# This is a PUBLIC DOMAIN code written by Wojciech M. Zabolotny (wzab@ise.pw.edu.pl)
from i2c_obj import *
class i2c_ADN4604(i2c_node):
    # __init__ is inherited from i2c_node
    def read(self, reg_nr):
        self.access()
        self.srv.i2c_write(self.address, (reg_nr, ))
        return self.srv.i2c_single_read(self.address)

    def write(self, reg_nr,  val):
        self.access()
        self.srv.i2c_write(self.address,  (reg_nr,  val))
    
    def dump_regs(self,  first,  last,  step):
        ad = first
        while ad <= last:
            print("%x:%x" % (ad,  self.read(ad)))
            ad  += step



