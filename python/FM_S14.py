# This is a PUBLIC DOMAIN code written by Wojciech M. Zabolotny (wzab@ise.pw.edu.pl)
from i2c_obj import *
class i2c_FMS14Q(i2c_node):
    def write_reg(self, adr,  val):
        self.srv.i2c_write(self.address,  (adr , val, ))
    def read_reg(self, adr):
        self.srv.i2c_write(self.address, (adr, ))
        return self.srv.i2c_single_read(self.address)
    def set_frq(self, frq):
        self.access()
        #Read settings for 0
        r0 = self.read_reg(0)
        cp0 = r0 >> 6
        mint0 = (r0 & 0x3e)>>1
        frac0 = r0 & 1
        adr = 4
        while adr <= 11:
            frac0 *= 256
            frac0 |= self.read_reg(adr)
            adr += 4
        r12 = self.read_reg(12)
        frac0 = (frac0 * 2) | (r12 >> 7)
        n0 = r12 & 0x7f
        r20 = self.read_reg(20)
        p0 = r20 >> 6
        p0v = (1,  2,  4,  5)[p0]
        mint0 = mint0 | (r20 & 0x20)
        mtot = mint0+(frac0*(1.0/(1<<18)))
        print("p0=%g p0v=%g n0=%g mint0=%g frac0=%g mtot=%g" % (p0,  p0v,  n0,  mint0,  frac0,  mtot))
        fout = 212.5e6
        fref = fout*n0/mtot
        print("fref=%g" % fref)
        #Now we look for the right divisor
        found = 0
        P = 0
        while P<=3:
            PV = (1,  2,  4,  5)[P]
            N = 2
            while N <= 126:
                fvco = float(N) * PV * frq
                if (fvco >= 1.95e9) & (fvco <= 2.6e9):
                    found = 1
                    break
                if N<6:
                    N+=1
                else :
                    N += 2
            if found==1:
                break
            P += 1
        #Check if the proper value was found
        if found==0:
            raise Exception("Proper value of N not found")
        else:
            print("fvco=%g N=%g P=%g" % (fvco,  N,  P))
        #Find the appropriate M
        M = float(fvco) / fref
        #Divide M into integer and fractional part
        MINT = int(M)
        MFRAC = M - MINT
        #Shift bits appropriately
        MFRAC = int(MFRAC * (1<<18) + 0.5)
        print("N=%g P=%g PV=%g MINT=%g MFRAC=%g" % (N,  P,  PV,  MINT, MFRAC))
        #Now write the new settings back to the hardware, to channel 3
        #CP copy from channel 0
        r3 = (cp0 << 6) | ((MINT & 0x1f)<<1) | ((MFRAC & 0x20000)>>17)
        self.write_reg(3,  r3)
        r7 = (MFRAC >> 9) & 0xff
        self.write_reg(7,  r7)
        r11 = (MFRAC >> 1) & 0xff
        self.write_reg(11,  r11)
        r15 = ((MFRAC & 0x01)<<7) | (N & 0x7f)
        self.write_reg(15 , r15)
        #For r23 copy to channel 3 values from channel 0
        r23 = self.read_reg(20)
        #Now set only bits for P and MINT[5]
        r23 = (r23 & 0x1f) | (P<<6) | (MINT & 0x20)
        self.write_reg(23,  r23)
        #Toggle the FSEL bits
        r18 = self.read_reg(18)
        #Clear those bits
        self.write_reg(18,  r18 & 0xe7)
        #set those bits
        self.write_reg(18,  r18 | 0x18)

