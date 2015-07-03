#!/bin/bash
#Modify the path below
XIL_ISE_PATH=/home/xl/Xilinx/14.7/ISE_DS/
(
 source $XIL_ISE_PATH/settings64.sh
 impact -batch convert.cmd
)
