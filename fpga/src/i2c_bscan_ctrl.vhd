-------------------------------------------------------------------------------
-- Title      : I2C controller driven by BSCANE2 
-- Project    : 
-------------------------------------------------------------------------------
-- File       : i2c_vio_ctrl_top.vhd
-- Author     : Wojciech M. Zabolotny wzab01<at>gmail.com
-- License    : PUBLIC DOMAIN
-- Company    : 
-- Created    : 2015-05-03
-- Last update: 2015-07-02
-- Platform   : 
-- Standard   : VHDL'93/02
-------------------------------------------------------------------------------
-- Description:
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

entity i2c_bscan_ctrl is
  generic (
    NUM_I2CS : integer := 5);
  port (
    frq0 : in    std_logic_vector(31 downto 0);
    frq1 : in    std_logic_vector(31 downto 0);
    frq2 : in    std_logic_vector(31 downto 0);
    clk  : in    std_logic;
    --rst_p : in    std_logic;
    scl  : inout std_logic_vector(NUM_I2CS-1 downto 0);
    sda  : inout std_logic_vector(NUM_I2CS-1 downto 0));

end entity i2c_bscan_ctrl;

architecture beh of i2c_bscan_ctrl is

  signal i2c_sel : integer range 0 to NUM_I2CS-1 := 0;
  signal bus_sel : unsigned(2 downto 0)          := (others => '0');

  signal i2c_cs    : std_logic;
  signal din8      : std_logic_vector(7 downto 0);
  signal dout8     : std_logic_vector(7 downto 0);
  signal din       : std_logic_vector(31 downto 0);
  signal dout      : std_logic_vector(31 downto 0);
  signal ctrl_reg  : std_logic_vector(31 downto 0);
  signal addr      : std_logic_vector(3 downto 0);
  signal nrd, nwr  : std_logic;
  signal cs        : std_logic_vector(0 to 0);
  signal vclk      : std_logic;
  signal i2c_rst_n : std_logic_vector(0 to 0);
  signal vrst_n    : std_logic_vector(0 to 0);
  signal scl_i     : std_logic;
  signal scl_o     : std_logic;
  signal sda_i     : std_logic;
  signal sda_o     : std_logic;

  component i2c_bus_wrap is
    port (
      din    : in  std_logic_vector(7 downto 0);
      dout   : out std_logic_vector(7 downto 0);
      addr   : in  std_logic_vector(2 downto 0);
      rd_nwr : in  std_logic;
      cs     : in  std_logic;
      clk    : in  std_logic;
      rst    : in  std_logic;
      scl_i  : in  std_logic;
      scl_o  : out std_logic;
      sda_i  : in  std_logic;
      sda_o  : out std_logic);
  end component i2c_bus_wrap;

begin  -- architecture beh

  process (bus_sel) is
    variable v_bus_sel : integer;
  begin  -- process
    v_bus_sel    := to_integer(unsigned(bus_sel));
    if v_bus_sel <= NUM_I2CS-1 then
      i2c_sel <= v_bus_sel;
    else
      i2c_sel <= 0;
    end if;
  end process;

  jtag_bus_ctl_1 : entity work.jtag_bus_ctl
    generic map (
      d_width => 32,
      a_width => 4)
    port map (
      din  => din,
      dout => dout,
      addr => addr,
      nwr  => nwr,
      nrd  => nrd);

  i2c_cs <= addr(3);
  dout8   <= dout(7 downto 0);
  -- Reading registers
  process (addr, din8, frq0, frq1, frq2)
  begin  -- process
    case addr is
      when x"0"   => din <= x"12ab3344";
      when x"1"   => din <= frq0;
      when x"2"   => din <= frq1;
      when x"3"   => din <= frq2;
      when x"4"   => din <= std_logic_vector(resize(bus_sel, 32));
      when x"5"   => din <= ctrl_reg;
      when others => null;
    end case;
    if addr(3) = '1' then
      din             <= (others => '0');
      din(7 downto 0) <= din8;
    end if;
  end process;

  -- Writing to registers
  p1 : process (nwr)
  begin  -- process p1
    if nwr'event and nwr = '1' then     -- rising clock edge
      case addr is
        when x"4"   => bus_sel  <= unsigned(dout(2 downto 0));
        when x"5"   => ctrl_reg <= dout;
        when others => null;
      end case;
    end if;
  end process p1;

  i2c_bus_wrap1 : entity work.i2c_bus_wrap
    port map (
      din     => dout8,
      dout    => din8,
      addr    => addr(2 downto 0),
      nwr     => nwr,
      nrd     => nrd,
      cs      => i2c_cs,
      clk     => vclk,
      rst     => ctrl_reg(0),
      i2c_rst => ctrl_reg(1),
      scl_i   => scl_i,
      scl_o   => scl_o,
      sda_i   => sda_i,
      sda_o   => sda_o);

  vclk <= clk;

  process (i2c_sel, scl, scl_o, sda, sda_o) is
  begin  -- process
    scl_i <= scl(i2c_sel);
    sda_i <= sda(i2c_sel);
    for i in 0 to NUM_I2CS-1 loop
      if i = i2c_sel then
        if scl_o = '0' then
          scl(i) <= '0';
        else
          scl(i) <= 'Z';
        end if;
        if sda_o = '0' then
          sda(i) <= '0';
        else
          sda(i) <= 'Z';
        end if;
      else
        scl(i) <= 'Z';
        sda(i) <= 'Z';
      end if;
    end loop;  -- i    
  end process;

end architecture beh;

