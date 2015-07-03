# This is a PUBLIC DOMAIN code written by Wojciech M. Zabolotny (wzab@ise.pw.edu.pl)
from i2c_obj import *
class i2c_Si57x(i2c_node):
    # __init__ is inherited from i2c_node
    def write_reg(self, adr,  val):
        self.srv.i2c_write(self.address,  (adr , val, ))
    def read_reg(self, adr):
        self.srv.i2c_write(self.address, (adr, ))
        return self.srv.i2c_single_read(self.address)
    def set_frq(self,  frq):
        self.access()
        #Reset Silabs to initial settings
        self.write_reg(0x87,  0x01)
        #Now read rfreq
        r7=self.read_reg(7)
        hsdiv = (r7 & 0xe0)>>5
        hsdiv = hsdiv+4
        n1 = (r7 & 0x1f)<<2
        r8  = self.read_reg(8)
        n1 |= ((r8 & 192)>>6)
        n1 += 1
        rfreq = r8 & 63
        adr = 9
        while adr<=12:
            rfreq = rfreq << 8
            rfreq |= self.read_reg(adr)
            adr += 1
        fxtal = (1<<28)*100e6/rfreq*hsdiv*n1
        #Print the xtal frequency
        print("fxtal=%g frq=%g" % (fxtal,  frq))
        #Calculate the new values
        #To minimize the power consumption, we look for the minimal
        #value of N1 and maximum value of HSDIV, keeping the 
        #DCO=frq*N1*HSDIV in range 4.85 to 5.67 GHz
        #We browse possible values of N1 and hsdiv looking for the best
        #combination
        #Below is the list of valid N1 values
        hsdvals = ((7,  11.0),  (5,  9.0), (3,  7.0), (2,  6.0) , (1,  5.0),  (0,  4.0))
        found = 0
        for hsdl in hsdvals:
            hsdr =hsdl[0]
            hsdv = hsdl[1]
            print("hsdr=%g hsdv=%g" % (hsdr,  hsdv))
            #Now we check possible hsdiv values and take the greatest
            #matching the condition
            n1v = 1
            while n1v<=128:
                fdco = frq * n1v
                fdco = fdco * hsdv
                print("frq=%g fdco=%g n1v=%g hsdv=$%g" % (frq,  fdco,  n1v,  hsdv))
                if (fdco >= 4.85e9) & (fdco <= 5.67e9):
                    found = 1
                    break
                if n1v<2:
                    n1v += 1
                else:
                    n1v += 2
            if found==1:
                break
        #Check if the proper value was found
        if found==0:
            raise Exception("Proper values N1 HSDIV not found")
        else:
            print("fdco=%g N1=%g HSDIV=%g" % (fdco,  n1v,  hsdv))
        #Calculate the nfreq
        nfreq = int(fdco*(1<<28)/fxtal + 0.5)
        print("%x" % nfreq)
        self.write_reg(0x89, 0x10)
        self.write_reg(0x87,  0x30)
        #Decrement n1v, before writing to the register
        n1v -= 1
        #Now store the values
        r7 = (hsdr << 5) | (n1v>>2)
        print("r7: %x" % r7)
        self.write_reg(7,  r7)
        adr=12
        while adr>8:
            rval= nfreq & 255
            print ("r%d: %x" % (adr,  rval))
            self.write_reg(adr,  rval)
            nfreq = nfreq >> 8
            adr -= 1
        rval = ((n1v & 0x3)<<6) | nfreq
        self.write_reg(8,  rval)
        print("r8: %x" % rval)
        self.write_reg(0x89,  0x00)
        self.write_reg(0x87,  0x40)
 
