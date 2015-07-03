from i2c_obj import *
class i2c_ctrl(my_object):
    def __init__(self,bctl, base):
        self.base = base
        self.bctl = bctl
    def start(self):
        self.reg_write(0, 200)
        self.reg_write(1, 0)
        self.reg_write(2, 128)
    def reg_write(self, ad, dta):
        self.bctl.jt_write(self.base+ad,dta)
    def reg_read(self, ad):
        #Because there is no way to add the wait state in the JTAG access,
        #We do a dirty trick - read 2 times
        self.bctl.jt_read(self.base+ad)
        return self.bctl.jt_read(self.base+ad)
    def i2c_write(self, ad, dta):
        self.reg_write(3,ad << 1)
        self.reg_write(4,128 | 16)
        # Cmd: STA+WR
        #Wait for ACK
        while True:
            st=self.reg_read(4)
            if st & 2 == 0:
                break
        if st & 128 != 0:
            #Error - NACK
            raise Exception("NACK in address")
        i=len(dta)
        for d in dta:
            i=i-1
            self.reg_write(3,d)
            if i==0:
                self.reg_write(4, 64 | 16)
            else:
                self.reg_write(4, 16)
            while True:
                st=self.reg_read(4)
                if st & 2 == 0:
                    break
            if st & 0x80 != 0:
                #Error - NACK
                raise Exception("NACK in data")
                
    def i2c_single_read(self, ad):
        self.reg_write(3,(ad << 1)|1)
        self.reg_write(4,128 | 16)
        # Cmd: STA+WR
        #Wait for ACK
        while True:
            st=self.reg_read(4)
            if st & 2 == 0:
                break
        if st & 128 != 0:
                #Error - NACK
            raise Exception("NACK in address")
        self.reg_write(4, 64 | 32 | 8)
        while True:
            st=self.reg_read(4)
            if st & 2 == 0:
                break
        return self.reg_read(3)

    def i2c_multi_read(self, ad, num):
        self.reg_write(3,(ad << 1)|1)
        self.reg_write(4,128 | 16)
        # Cmd: STA+WR
        #Wait for ACK
        while True:
            st=self.reg_read(4)
            if st & 2 == 0:
                break
        if st & 128 != 0:
                #Error - NACK
            raise Exception("NACK in address")
        res = []
        while num > 0:
            self.reg_write(4, 64 | 32 | 8)
            while True:
                st=self.reg_read(4)
                if st & 2 == 0:
                    break
            res.append(self.reg_read(3))
            if st & 128 != 0:
                #NACK - no more data
                break
            num = num - 1
        return res
