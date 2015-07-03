setMode -bs
setCable -port svf -file "AFCK_i2c_bscan_ctrl.svf"
addDevice -p 1 -file "i2c_bscan_ctrl_top.bit"
Program -p 1 
quit

