-------------------------------------------------------------------------------
-- Title      : jtag_bus_ctl - interface between the JTAG and internal bus
--              adapted for Kintex 7
-- Project    : 
-------------------------------------------------------------------------------
-- File       : jtag_bus_ctl.vhd
-- Author     : Wojciech M. Zabolotny
-- License    : PUBLIC DOMAIN
-- Company    : 
-- Created    : 2009-10-13
-- Last update: 2015-05-17
-- Platform   : 
-- Standard   : VHDL'93
-------------------------------------------------------------------------------
-- Description: This is implementation of the bus controller for Xilinx FPGAs
--              allowing you to access the internal bus via JTAG
--              The internal bus uses:
--                 addr(a_width-1 downto 0) - address lines
--                 dout(d_width-1 downto 0) - data to be written to register
--                                            on the internal bus
--                 din(d_width-1 downto 0)  - data read from the register on
--                                            on the internal bus
--                 nrd - asynchronous read strobe
--                 nwr - asynchronous write strobe
--
--              This implementation uses one JTAG instruction:
--              USER1 - dr length: max(2+a_width,1+d_width)
--                  data transferred for this instruction may be:
--                  (xxx: optional filler)
--                  10_xxx_address - READ command with address
--                  11_xxx_address - WRITE command with address
--                  00_xxx_data - DATA word to be written or dummy data in case
--                                of read access - no change of address
--                                THIS WORD MAY BE USED AFTER THE READ COMMAND
--                                TO READ THE DATA WITHOUT ISSUING A NEW COMMAND
--                  01_xxx_data - DATA word to be written or dummy data in case
--                                of read access - the access address gets
--                                incremented afterwards!
--
--              Due to the way the JTAG works, the read data are transferred
-- when next command or data word is shifted through the dr register.
--
--              It is perfectly OK to issue the READ command, and then WRITE command
--              The read data will be transferred when WRITE command is transmitted.
--
--              The write command must be followed by the data command (you may
--              issue a few data commands in sequence generating a few writes
--              to the same address - useful for bit-banging procedures).
--
--              If you want to read data without issuing the next command - send
--              the DATA word 00_??? after the READ command. Please note, that
--              multiple DATA 00_??? words after the READ command do not allow
--              you to perform multiple reads! The first DATA word cancells
--              the READ mode to NOOP mode.
--              If you want to read the same address multiple times - you should
--              issue multiple READ commands with the same address (it does not
--              affects performance, as you always have to send new word to receive
--              the data)
--
--              If you want to read a few consecutive registers, then you
--              should issue the READ command with the address of the first
--              register, then multiple 01_???? DATA words to read data and
--              increase address, and finally 00_???? DATA word to receive
--              the value read from the last register without triggering a new
--              read operation.
--
--              If you want to write data to a few consecutive registers, then
--              you should issue the WRITE command with the address of the first
--              register and then multiple 01_???? DATA words. The last one
--              may be the 00_???? DATA word, but this is not necessary.
--
--              The strobes nrd and nwr are generated from the TAP controller states
--              so the JTAG frequency affects the length ofread/write pulses
-------------------------------------------------------------------------------
-- Copyright (c) 2009 Wojciech M. Zabolotny (wzab<at>ise.pw.edu.pl) 
-------------------------------------------------------------------------------
-- Revisions  :
-- Date        Version  Author  Description
-- 2009-10-13  1.0      wzab      Created
-------------------------------------------------------------------------------
--
--  This program is PUBLIC DOMAIN code
--  You can do with it whatever you want, however NO WARRANTY of ANY KIND
--  is provided
--
-- 

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.std_logic_unsigned.all;
library work;

entity jtag_bus_ctl is
  generic (
    d_width : integer := 8;
    a_width : integer := 8);
  port (
    din : in std_logic_vector((d_width-1) downto 0);
    dout : out std_logic_vector((d_width-1) downto 0);
    addr : out std_logic_vector((a_width-1) downto 0);
    nwr : out std_logic;
    nrd : out std_logic
    );
end jtag_bus_ctl;

architecture syn of jtag_bus_ctl is

  component BSCANE2
    generic (
      JTAG_CHAIN : integer);
    port (
      CAPTURE : out std_ulogic;
      DRCK : out std_ulogic;
      RESET : out std_ulogic;
      RUNTEST : out std_ulogic;
      SEL : out std_ulogic;
      SHIFT : out std_ulogic;
      TCK : out std_ulogic;
      TDI : out std_ulogic;
      TMS : out std_ulogic;
      UPDATE : out std_ulogic;
      TDO : in std_ulogic);
  end component;

  signal jt_shift, jt_update, jt_tdi, jt_tdo, jt_tck, jt_tms, jt_drck,
    jt_capture, jt_sel, jt_reset : std_ulogic;  -- := '0';

  function maximum(L, R : integer) return integer is
  begin
    if L > R then
      return L;
    else
      return R;
    end if;
  end;

  constant DR_SHIFT_LEN : integer := maximum(a_width+2, d_width+2);
  -- Register storing the access address and mode (read/write)
  signal dr_shift : std_logic_vector(DR_SHIFT_LEN-1 downto 0) := (others => '0');
  signal write_addr, read_addr : std_logic_vector(a_width-1 downto 0);
  -- Register storing the data
  signal write_cmd, read_cmd : std_logic := '0';

begin

  BSCANE2_1 : BSCANE2
    generic map (
      JTAG_CHAIN => 1)
    port map (
      CAPTURE => jt_CAPTURE,
      DRCK => jt_DRCK,
      RESET => jt_RESET,
      SEL => jt_SEL,
      SHIFT => jt_SHIFT,
      TCK => jt_TCK,
      TDI => jt_TDI,
      TMS => jt_TMS,
      UPDATE => jt_UPDATE,
      TDO => jt_TDO);


  -- Generate the read strobe for external bus
  nrd <= '0' when jt_capture = '1' and jt_sel = '1' and read_cmd = '1' else '1';
  -- Generate the write strobe for the external bus - when write_cmd, and this
  -- is the data word
  nwr <= '0' when jt_update = '1' and jt_sel = '1' and
         write_cmd = '1' and dr_shift(DR_SHIFT_LEN-1) = '0' else '1';

  dout <= dr_shift(d_width-1 downto 0);
  addr <= write_addr when write_cmd = '1' else read_addr;

  -- Load and shift data to dr_addr_and_mode register
  pjtag1 : process (jt_drck, jt_reset)
  begin  -- process
    if jt_reset = '1' then
      dr_shift <= (others => '0');
    elsif jt_drck'event and jt_drck = '1' then  -- falling clock edge - state
      if jt_shift = '0' then
        if read_cmd = '1' then
          -- Read the data
          dr_shift(d_width-1 downto 0) <= din;
        end if;
      else
        -- Transfer the read_addr to the write_addr
        -- this is necessary to avoid updating the write_addr
        -- at the begining or end of the write cycle in the autoincrement mode
        write_addr <= read_addr;
        -- Shift the register
        dr_shift(DR_SHIFT_LEN-1) <= jt_tdi;
        for i in 0 to DR_SHIFT_LEN-2 loop
          dr_shift(i) <= dr_shift(i+1);
        end loop;  -- i
      end if;
    end if;
  end process pjtag1;

  pupd1a : process(jt_reset, jt_update)
  begin  -- process
    if jt_reset = '1' then
    elsif jt_update'event and jt_update = '1' then
      if jt_sel = '1' then
        if dr_shift(DR_SHIFT_LEN-1 downto DR_SHIFT_LEN-2) = "10" then
          read_cmd <= '1';
          write_cmd <= '0';
          read_addr <= dr_shift(a_width-1 downto 0);
        elsif dr_shift(DR_SHIFT_LEN-1 downto DR_SHIFT_LEN-2) = "11" then
          -- Write access
          read_cmd <= '0';
          write_cmd <= '1';  -- We PREPARE to write
          read_addr <= dr_shift(a_width-1 downto 0);
          -- we can not write the write_addr here
          -- It will be updated from the read_addr in another process
          -- this is needed to implement the autoincrement mode!
        elsif dr_shift(DR_SHIFT_LEN-1 downto DR_SHIFT_LEN-2) = "00" then
          -- Data
          read_cmd <= '0';  -- Block further READs
        else
          -- "01" - This is the autoincrement mode! we should increment
          -- the address, but the write cycle is still active!
          -- to avoid problems with the hold time we update now only the read address
          read_addr <= write_addr+1;
          -- the write address will be updated later, when shifting the next word
        end if;
      end if;
    end if;
  end process pupd1a;

  -- No update process is needed! Our controller just generates the nwr pulse
  -- for internal logic

--  pupd1b : process(jt_reset, jt_update)
--  begin  -- process
--    if jt_reset = '1' then
--      null;
--    elsif jt_update'event and jt_update = '0' then
--      if jt_sel1 = '1' then
--        null;
--      end if;
--    end if;
--  end process pupd1b;

  jt_TDO <= dr_shift(0);
end syn;
