#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This file implements classes responsible for access to different objects connected to the I2C bus
"""
from KX1_Exceptions import *
import KX1_srv
import xml.etree.ElementTree as ET
import traceback
#host="192.168.228.2"
#host="localhost"
#port=34321
#main_srv = KX1_srv.KX1_srv(host,port)
"""
Implementation of logging
Each object, which must log information
should be connected to the root logger.

The logging hierarchy is not necessarily associated with the I2C hierarchy!

"""

# The class my_object is just workaround for problem, that __init__ in object
# does not accept parameters.
class my_object(object):
    def __init__(self, *a, **kw):
        super(my_object, self).__init__()

class log_node(my_object):
    def __init__(self,  *a,  **kw):
        super(log_node, self).__init__(*a, **kw)
        self.log_children = []
        if kw.has_key('log'):
            """
            The "log" argument should be a tupple consisting of the
            log parent and node name.
            """
            log=kw['log']
            self.log_name=log[1]
            if log[0] != None:
                log[0].log_add(self)
                print 'added '+self.log_name+ ' to '+log[0].log_name

    def log_create(self, parent):
        #First create your XML node
        n = ET.SubElement(parent, self.log_name)
        #Add attributes to your own node
        if hasattr(self,  'valid') and not self.valid:
            # Node itself is not valid
            n.attrib["INVALID"]=self.exc
        else:
            try:
                self.log_report(n)
            except  Exception as e:
                n.attrib["EXCEPTION"]=traceback.format_exc(e)
            #Now iterate over chilldren (if there are any) and add their nodes
            for c in self.log_children:
                c.log_create(n)
        return n

    def log_add(self, log_child):
        self.log_children.append(log_child)

    def log_report(self,  node):
        #If not overriden, should do nothing
        return



class i2c_root(my_object):

#Class i2c_root implements the root of the I2C tree

    def __init__(self,  *a, **kw):
        super(i2c_root, self).__init__(*a, **kw)
        self.parent = None
        self.children=[]
        self.branch_num = None
        self.selected_branch = None
        self.srv = kw['server']
    def add_child(self,child):
        self.children.append(child)
    def reset_switch(self):
        for c in self.children:
            if c.valid:
               c.reset_switch()
    def set_access(self, branch_num):
        return

class i2c_node(my_object):

#Class i2c_node implements the node in the I2C tree

    def __init__(self,  *a,  **kw):
        super(i2c_node, self).__init__(*a, **kw)
        self.parent=kw['branch'][0]
        self.parent.add_child(self)
        self.children=[]
        self.branch_num=kw['branch'][1]
        self.srv = self.parent.srv
        self.selected_branch = None
        if kw.has_key('address'):
            self.address = kw['address']
        #Check if there is a user provided init function
        self.valid=True
        try:
            user_init=self.my_init
            #There is __my_init function, so the node is invalid if it is not called successfully
            self.valid=False
            try:
                self.my_init(*a,  **kw)
                self.valid=True
            except Exception:
                self.valid = False
                self.exc=traceback.format_exc()
        except Exception:
            pass
        
    def add_child(self,child):
        self.children.append(child)
    def reset_switch(self):
        self.selected_branch = None
        for c in self.children:
            c.reset_switch()
    def set_access(self,  branch_num):
        raise KX1_Control_Error("This function should never be called! It should be overriden!")

    def access(self):
        if self.branch_num != None:
            #Ensure, that we can access the parent
            self.parent.access()
        #switch on our branch in the parent
        #print str(self.parent) + "," + str(self.branch_num)
        if self.parent.selected_branch != self.branch_num:
            self.parent.set_access(self.branch_num)
            self.parent.selected_branch = self.branch_num
            #print "missed!"
        else:
            #print "hit!"
            pass
        return

class i2c_root_switch(i2c_node):
    # __init__ is inherited from i2c_node
    def set_access(self, branch_num):
        self.srv.fi2c_sel(branch_num)

class i2c_pca9547bs(i2c_node):
    # __init__ is inherited from i2c_node
    def set_access(self, branch_num):
        self.srv.fi2c_mwrite(self.address, [8 | branch_num,])

class i2c_max7300(i2c_node):
    # __init__ is inherited from i2c_node
    def output(self):
        self.access()
        self.srv.fi2c_mwrite(self.address, [0x04, 0x01])
        self.srv.fi2c_mwrite(self.address, [0x09, ]+7*[0x55])
    def set_led(self, led_number, state):
        self.access()
        self.srv.fi2c_mwrite(self.address, [0x2c+led_number,  state])

class i2c_lm75(i2c_node,  log_node):
    def __init__(self,*a, **kw):
        super(i2c_lm75,self).__init__(*a, **kw)

    def get_conf(self):
        self.access()
        self.srv.fi2c_mwrite(self.address, [1,])
        t=self.srv.fi2c_mread(self.address, 1)
        return t[0]

    def get_temp(self):
        self.access()
        self.srv.fi2c_mwrite(self.address, [0,])
        t=self.srv.fi2c_mread(self.address, 2)
        return t[0]+(t[1] & 0x80)/256.0

    def get_thyst(self):
        self.access()
        self.srv.fi2c_mwrite(self.address, [2,])
        t=self.srv.fi2c_mread(self.address, 2)
        return t[0]+(t[1] & 0x80)/256.0

    def get_tos(self):
        self.access()
        self.srv.fi2c_mwrite(self.address, [3,])
        t=self.srv.fi2c_mread(self.address, 2)
        return t[0]+(t[1] & 0x80)/256.0

    def set_conf(self, conf):
        self.access()
        self.srv.fi2c_mwrite(self.address, [1, conf, ])

    def set_thyst(self, temp):
        t=[2, int(temp),  128*(int(temp*2+0.5) % 2)]
        self.access()
        self.srv.fi2c_mwrite(self.address, t)

    def set_tos(self, temp):
        t=[int(temp),  128*(int(temp*2+0.5) % 2)]
        self.access()
        self.srv.fi2c_mwrite(self.address, 3, t)
    #Log values
    def log_report(self,  node):
        node.attrib["T"]=str(self.get_temp())



class i2c_ina220(i2c_node,  log_node):
    # __init__ is inherited from i2c_node
    def __init__(self,*a, **kw):
        super(i2c_ina220,self).__init__(*a, **kw)
    def my_init(self,  *a,  **kw):
        print "I got called!!!"
        self.rshunt=kw['rshunt']
        self.make_conf(brng=1,pg=0,badc=15,sadc=15,mode=7)

    def make_conf(self,rst=0,brng=0,pg=0,badc=3,sadc=3,mode=7):
        conf=((rst & 0b1)<<15) | ((brng & 0b1) << 13) | ((pg & 0b11)<<11) | \
             ((badc & 0b1111)<<7) | ((sadc & 0b1111)<<3)|((mode & 0b111) << 0)
        self.set_conf(conf)
    def set_conf(self, conf):
        self.access()
        self.srv.fi2c_mwrite(self.address, [0, (conf >> 8) & 0xff,  conf & 0xff, ])
    def set_cal(self, cal):
        self.access()
        self.srv.fi2c_mwrite(self.address, [5, (cal >> 8) & 0xff,  cal & 0xff, ])
    def get_conf(self):
        self.access()
        self.srv.fi2c_mwrite(self.address, [0,])
        t=self.srv.fi2c_mread(self.address, 2)
        return (t[0]<<8)+t[1]
    def get_I_Vshunt(self):
        self.access()
        self.srv.fi2c_mwrite(self.address, [1,])
        t=self.srv.fi2c_mread(self.address, 2)
        t=(t[0]<<8)+t[1]
        if t & 0x8000:
            t=t-0x10000
        return t*320e-3/32000.0/self.rshunt

    def get_Vbus(self):
        self.access()
        self.srv.fi2c_mwrite(self.address, [2,])
        t=self.srv.fi2c_mread(self.address, 2)
        return (((t[0]<<8)+t[1])>>3)*32.0/8000.0

    def get_power(self):
        self.access()
        self.srv.fi2c_mwrite(self.address, [3,])
        t=self.srv.fi2c_mread(self.address, 2)
        return (t[0]<<8)+t[1]

    def get_current(self):
        self.access()
        self.srv.fi2c_mwrite(self.address, [4,])
        t=self.srv.fi2c_mread(self.address, 2)
        return (t[0]<<8)+t[1]

    def get_cal(self):
        self.access()
        self.srv.fi2c_mwrite(self.address, [5,])
        t=self.srv.fi2c_mread(self.address, 2)
        return (t[0]<<8)+t[1]

    #Log values
    def log_report(self,  node):
        node.attrib["V"]=str(self.get_Vbus())
        node.attrib["I"]=str(self.get_I_Vshunt())

class i2c_mcp23017(i2c_node):
    pass

class i2c_ads1015(i2c_node,  log_node):
    def __init__(self,*a, **kw):
        super(i2c_ads1015,self).__init__(*a, **kw)
    def my_init(self,  *a,  **kw):
        self.sens=kw['sens']

    def set_conf(self,val):
        self.access()
        self.srv.fi2c_mwrite(self.address,[1,(val>>8)&0xff, val & 0xff,])

    def set_conf_adv(self,os=1,mux=0,pga=1,mode=1,dr=0b11,comp_mode=0,comp_pol=0,comp_lat=0,comp_queue=0):
        self.access()
        val = ((os & 0b1)<<15)|((mux & 0b111)<<12)|((pga & 0b111)<<9) | \
              ((mode & 0b1)<<8)|((dr & 0b111)<<5)|((comp_mode & 0b1)<<4)| \
              ((comp_pol & 0b1)<<3)|((comp_lat & 0b1)<<2)|((comp_queue & 0b11)<<0)
        self.srv.fi2c_mwrite(self.address,[1,(val>>8)&0xff, val & 0xff,])

    def get_conf(self):
        self.access()
        self.srv.fi2c_mwrite(self.address,[1,])
        t = self.srv.fi2c_mread(self.address,2)
        return (t[0]<<8)+t[1]

    def get_adcval(self):
        self.access()
        self.srv.fi2c_mwrite(self.address,[0,])
        res=self.srv.fi2c_mread(self.address,2)
        res=(res[0]<<8) | res[1]
        return res

    def get_adc_simple(self,channel):
        self.set_conf_adv(os=1,mux=channel | 0b100,pga=0b001)
        while True:
            res=self.get_conf()
            #print hex(res)
            if res & 0x8000:
                break
            else:
                print "."
        res=self.get_adcval()
        #print hex(res)
        if res & 0x8000:
            res=res-0x10000
        #
        res=res*(4.096/0x8000)
        res=res*self.sens[channel][0]+self.sens[channel][1]
        return res

            #Log values
    def log_report(self,  node):
        for i in range(0, 4):
            node.attrib["V"+str(i)]=str(self.get_adc_simple(i))

    pass

"""
Jak tu reprezentować oddzielnie switch PCA9547BS, a oddzielnie "branche?"
Każdy obiekt
"""
class i2c_board:
    pass

class KX1_sensors(object):
    def __init__(self, main_srv):
        self.srv=main_srv
        backplane=log_node(log=(None, 'SYS'))
        r1=i2c_root(server=main_srv)
        rs1=i2c_root_switch(branch=(r1, None))
        b_sys=(rs1, 1)
        b_fmc=(rs1, 0)
        s_sys=i2c_pca9547bs(branch=b_sys, address=0x70)
        s_fmc=i2c_pca9547bs(branch=b_fmc, address=0x74)
        b_mb=(s_sys, 4)
        b_fmc=(s_fmc, 3)
        lm_pcie=i2c_lm75(branch=b_mb, address=0b1001100, log=(backplane,'TEMP_PCIe'))
        lm_dcdc=i2c_lm75(branch=b_mb, address=0b1001101, log=(backplane, 'TEMP_DCDC'))
        lm_board=i2c_lm75(branch=b_mb, address=0b1001110, log=(backplane,'TEMP_BOARD'))
        lm_fpga=i2c_lm75(branch=b_mb, address=0b1001111, log=(backplane,'TEMP_FPGA'))
        #ina_fmc_3V3=i2c_ina220(branch=b_mb, 0b1001001,2e-3)
        #ina_fmc_2V5=i2c_ina220(branch=b_mb, 0b1001000,2e-3)
        #ina_fmc_P12V=i2c_ina220(branch=b_mb, 0b1000000,2e-3)
        #ina_P1V0=i2c_ina220(branch=b_mb, 0b1000001,0.5e-3)
        ina_P3V3=i2c_ina220(branch=b_mb, address=0b1000010,rshunt=1e-3, log=(backplane,'P3V3'))
        ina_P1V2=i2c_ina220(branch=b_mb, address=0b1000011,rshunt=1e-3, log=(backplane,'P1V1'))
        ina_P1V5=i2c_ina220(branch=b_mb, address=0b1000100,rshunt=1e-3, log=(backplane,'P1V5'))
        ina_P2V5=i2c_ina220(branch=b_mb, address=0b1000101,rshunt=1e-3, log=(backplane,'P2V5'))
        ina_P3V3=i2c_ina220(branch=b_mb, address=0b1000110,rshunt=2e-3, log=(backplane,'SLOT_P3V3'))
        #ina_pcie_P2V5=i2c_ina220(b_mb, 0b1000111,1e-3)
        b_car=((s_sys,0),(s_sys,1),(s_sys,2),(s_sys,3))
        b_carfmc=((s_fmc,0),(s_fmc,1),(s_fmc,2),(s_fmc,3))
        cars=[]
        fmcs=[]
        #Sensitivity table for ADCs on FMCs - coefficients of the linear function
        fmc_adc_sens=((15.1/5.1,0),(23.0/5.0,-18*2.048/5.0),(15.1/5.1,0),(25.1/5.1,0))
        for i in range(0,4):
            cars.append(i2c_board())
            logx=log_node(log=(backplane, 'CAR'+str(i)))
            cars[i].lm_fmc1=i2c_lm75(branch=b_car[i],address=0b1001011, log=(logx, 'TMP_FMC1'))
            cars[i].lm_fmc2=i2c_lm75(branch=b_car[i],address=0b1001100, log=(logx, 'TMP_FMC2'))
            cars[i].lm_fmc3=i2c_lm75(branch=b_car[i],address=0b1001110, log=(logx, 'TMP_FMC3'))
            cars[i].lm_fmc4=i2c_lm75(branch=b_car[i],address=0b1001111,  log=(logx, 'TMP_FMC4'))
            cars[i].lm_fpga=i2c_lm75(branch=b_car[i],address=0b1001101,  log=(logx, 'TMP_FPGA_SDRAM'))
            cars[i].ina_fmc_P12V=i2c_ina220(branch=b_car[i],address=0b1000000,rshunt=2e-3, log=(logx, 'FMC_P12V'))
            cars[i].ina_P1V5=i2c_ina220(branch=b_car[i],address=0b1000001,rshunt=1e-3, log=(logx, 'P1V5'))
            cars[i].ina_P2V5=i2c_ina220(branch=b_car[i],address=0b1000010,rshunt=1e-3, log=(logx, 'P2V5'))
            cars[i].ina_fmc34_P3V3=i2c_ina220(branch=b_car[i],address=0b1000011,rshunt=1e-3, log=(logx, 'FMC34_P3V3'))
            cars[i].ina_fmc12_P3V3=i2c_ina220(branch=b_car[i],address=0b1000100,rshunt=1e-3, log=(logx, 'FMC12_P3V3'))
            cars[i].ina_P1V2=i2c_ina220(branch=b_car[i],address=0b1000101,rshunt=1e-3, log=(logx, 'P1V2'))
            cars[i].s_fmc=i2c_pca9547bs(branch=b_carfmc[i],address=0b1110000)
            if i==3:
                b_led=(cars[i].s_fmc,7)
                leds=i2c_max7300(branch=b_led, address=0b1000101)
            for j in range(0,4):
                b_f = (cars[i].s_fmc,j)
                f=i2c_board()
                f.adc=i2c_ads1015(branch=b_f,address=0b1001000^(j % 2),sens=fmc_adc_sens, log=(logx, 'ADC'+str(j)))
                fmcs.append(f)
        self.root_log = backplane
        self.root_switch = r1

    def log(self):
        self.srv.fi2c_enable(25) #Set clock to 400kHz
        self.root_switch.reset_switch()
        v=ET.Element('LOG')
        r=self.root_log.log_create(v)
        return ET.tostring(v)
