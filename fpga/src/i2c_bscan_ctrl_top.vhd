-------------------------------------------------------------------------------
-- Title      : I2C controller driven by BSCANE2 object
-- Project    : 
-------------------------------------------------------------------------------
-- File       : i2c_bscan_ctrl_top.vhd
-- Author     : Wojciech M. Zabolotny wzab01<at>gmail.com
-- License    : PUBLIC DOMAIN
-- Company    : 
-- Created    : 2015-05-03
-- Last update: 2015-07-02
-- Platform   : 
-- Standard   : VHDL'93/02
-------------------------------------------------------------------------------
-- Description:
-- This core allows you to configure different programmable clocks in the AFCK
-- board.
-- The core measures the frequency of clock on the FPGA_CLK1_P(N) differen-
-- tial input.
-- The I2C may control one of five busses, depending on the value written
-- to the Vio_i2c_sel
-- Suggested method of operation:
-- 1) 
-------------------------------------------------------------------------------
-- Copyright (c) 2015 
-------------------------------------------------------------------------------
-- Revisions  :
-- Date        Version  Author  Description
-- 2015-05-03  1.0      wzab    Created
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library unisim;
use unisim.vcomponents.all;

entity i2c_bscan_ctrl_top is

  port (
    clk0_n      : in    std_logic;
    clk0_p      : in    std_logic;
    clk1_n      : in    std_logic;
    clk1_p      : in    std_logic;
    clk2_n      : in    std_logic;
    clk2_p      : in    std_logic;
    clk         : in    std_logic;
    -- Pin needed to enable switch matrix
    clk_updaten : out   std_logic;
    -- Pin needed to enable Si570
    si570_oe    : out   std_logic;
    --rst_p : in    std_logic;
    scl         : inout std_logic_vector(4 downto 0);
    sda         : inout std_logic_vector(4 downto 0));

end entity i2c_bscan_ctrl_top;

architecture beh of i2c_bscan_ctrl_top is

  constant NUM_I2CS : integer := 5;

  signal frq0_in  : std_logic;
  signal clk_frq0 : std_logic_vector(31 downto 0);
  signal frq1_in  : std_logic;
  signal clk_frq1 : std_logic_vector(31 downto 0);
  signal frq2_in  : std_logic;
  signal clk_frq2 : std_logic_vector(31 downto 0);


begin

  si570_oe    <= '1';
  clk_updaten <= '1';

  i2c_bscan_ctrl_1 : entity work.i2c_bscan_ctrl
    generic map (
      NUM_I2CS => NUM_I2CS)
    port map (
      frq0  => clk_frq0,
      frq1 => clk_frq1,
      frq2 => clk_frq2,
      clk => clk,
      scl => scl,
      sda => sda);

  ibufgds0 : IBUFDS port map(
    i  => clk0_p,
    ib => clk0_n,
    --ceb => '0',
    o  => frq0_in
    );
  ibufgds1 : IBUFDS_GTE2 port map(
    i   => clk1_p,
    ib  => clk1_n,
    ceb => '0',
    o   => frq1_in
    );
  ibufgds2 : IBUFDS_GTE2 port map(
    i   => clk2_p,
    ib  => clk2_n,
    ceb => '0',
    o   => frq2_in
    );

  frq_counter_0 : entity work.frq_counter
    generic map (
      CNT_TIME   => 20000000,
      CNT_LENGTH => 32)
    port map (
      ref_clk => clk,
      rst_p   => '0',
      frq_in  => frq0_in,
      frq_out => clk_frq0);

  frq_counter_1 : entity work.frq_counter
    generic map (
      CNT_TIME   => 20000000,
      CNT_LENGTH => 32)
    port map (
      ref_clk => clk,
      rst_p   => '0',
      frq_in  => frq1_in,
      frq_out => clk_frq1);

  frq_counter_2 : entity work.frq_counter
    generic map (
      CNT_TIME   => 20000000,
      CNT_LENGTH => 32)
    port map (
      ref_clk => clk,
      rst_p   => '0',
      frq_in  => frq2_in,
      frq_out => clk_frq2);

end architecture beh;

