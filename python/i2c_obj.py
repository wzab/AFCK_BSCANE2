#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This file implements classes responsible for access to different objects connected to the I2C bus
"""
import traceback
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

class i2c_root(my_object):

#Class i2c_root implements the root of the I2C tree

    def __init__(self,  *a, **kw):
        super(i2c_root, self).__init__(*a, **kw)
        self.parent = None
        self.children=[]
        self.branch_num = None
        self.selected_branch = None
        self.srv = kw['srv']
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
        raise Exception("This function should never be called! It should be overriden!")

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
        self.sel_branch(branch_num)

class i2c_pca9547bs(i2c_node):
    # __init__ is inherited from i2c_node
    def set_access(self, branch_num):
        self.srv.i2c_write(self.address, (8 | branch_num,))
