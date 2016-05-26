"""
Simple class to make construction and decoding of message bytes easier.

Based on APT Communication Protocol Rev. 7 (Thorlabs)

"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
import sys
import struct as st
from collections import namedtuple

_Message = namedtuple(
  '_Message',
  ['messageID', 'param1', 'param2', 'dest', 'src', 'data'])

class Message(_Message):
  @classmethod
  def unpack(cls, databytes, header_only=False):
    """
    pack() produces a string of bytes from a Message, pack() produces a
    Message from a string of bytes

    If header_only is True, then we will only attempt to decode the header,
    ignoring any bytes that follow, if any. This allows you get determine
    what the message is without having to read it in its entirety.

    Note that dest is returned AS IS, which means its MSB will be set if the
    message is more than just a header.
    """
    Header = namedtuple('Header', ['messageID', 'param1', 'param2', 'dest','src'])
    hd = Header._make(st.unpack('<HBBBB',databytes[:6]))

    # if MSB of dest is set, then there is additional data to follow
    if hd.dest & 0x80:
      datalen = hd.param1 | (hd.param2<<8)

      if header_only:
        data=None
      else:
        data=st.unpack('<%dB'%(datalen), databytes[6:])

      return Message( hd.messageID,
                      dest = hd.dest,
                      src = hd.src,
                      # we need these to be set since we need to know
                      # how long the data is when we decode only a header
                      param1 = hd.param1,
                      param2 = hd.param2,
                      data = data)
    else:
      return Message( hd.messageID,
                      param1 = hd.param1,
                      param2 = hd.param2,
                      dest = hd.dest,
                      src = hd.src)

  def __new__(cls, messageID, dest=0x50, src=0x01, param1=0, param2=0, data=None):
    assert(type(messageID) == int)
    if data:
      assert(param1 == 0 and param2 == 0)
      # assert(type(data) in [list, tuple, str])

      if type(data) == str:
        data = [ord(c) for c in data]

      return super(Message, cls).__new__(Message,
                                          messageID,
                                          None,
                                          None,
                                          dest,
                                          src,
                                          data)
    else:
      assert(type(param1) == int)
      assert(type(param2) == int)
      return super(Message, cls).__new__(Message,
                                          messageID,
                                          param1,
                                          param2,
                                          dest,
                                          src,
                                          None)

  def pack(self, verbose=False):
    """
    Returns a byte array representing this message packed in little endian
    """
    if self.data:
      """
      <: little endian
      H: 2 bytes for message ID
      H: 2 bytes for data length
      B: unsigned char for dest
      B: unsigned char for src
      %dB: %d bytes of data
      """
      datalen = len(self.data)
      if type(self.data) == str:
        datalist = list(self.data)
      else:
        datalist = self.data

      ret = st.pack(  '<HHBB%dB'%(datalen),
                      self.messageID,
                      datalen,
                      self.dest|0x80,
                      self.src,
                      *datalist)
    else:
      """
      <: little endian
      H: 2 bytes for message ID
      B: unsigned char for param1
      B: unsigned char for param2
      B: unsigned char for dest
      B: unsigned char for src
      """
      ret = st.pack(  '<HBBBB',
                      self.messageID,
                      self.param1,
                      self.param2,
                      self.dest,
                      self.src)
    if verbose:
      print(bytes(self),'=',[hex(ord(x)) for x in ret])

    return ret

  def __eq__(self, other):
    """
    We don't compare the underlying namedtuple because we consider data of
    [1,2,3,4,5] and (1,2,3,4,5) to be the same, while python doesn't.
    """
    return self.pack() == other.pack()

  @property
  def datastring(self):
    if (sys.version_info > (3, 0)):
      if type(self.data) == bytes:
        return self.data
      else:
        return self.data.encode()
    else:
      if type(self.data) == str:
        return self.data
      else:
        return ''.join(chr(x) for x in self.data)

  @property
  def datalength(self):
    if self.hasdata:
      if self.data:
        return len(self.data)
      else:
        return self.param1 | (self.param2<<8)
    else:
      return -1

  @property
  def hasdata(self):
    return self.dest & 0x80


def pack_unpack_test():
  """
  If we pack a message, then unpack it, we should recover the message exactly.
  """
  a = Message(0x0223,data=[1,2,3,4,5])
  s = a.pack(True)
  b = Message.unpack(s)
  assert a == b

MGMSG_HEADER_SIZE = 6

# Message codes for all the standard APT messages (only a small fraction of these are actually implemented)
MGMSG_MOD_IDENTIFY = 0x0223
MGMSG_MOD_SET_CHANENABLESTATE = 0x0210
MGMSG_MOD_REQ_CHANENABLESTATE = 0x0211
MGMSG_MOD_GET_CHANENABLESTATE = 0x0212
MGMSG_HW_DISCONNECT = 0x0002
MGMSG_HW_RESPONSE = 0x0080
MGMSG_HW_RICHRESPONSE = 0x0081
MGMSG_HW_START_UPDATEMSGS = 0x0011
MGMSG_HW_STOP_UPDATEMSGS = 0x0012
MGMSG_HW_REQ_INFO = 0x0005
MGMSG_HW_GET_INFO = 0x0006
MGMSG_RACK_REQ_BAYUSED = 0x0060
MGMSG_RACK_GET_BAYUSED = 0x0061
MGMSG_HUB_REQ_BAYUSED = 0x0065
MGMSG_HUB_GET_BAYUSED = 0x0066
MGMSG_RACK_REQ_STATUSBITS = 0x0226
MGMSG_RACK_GET_STATUSBITS = 0x0227
MGMSG_RACK_SET_DIGOUTPUTS = 0x0228
MGMSG_RACK_REQ_DIGOUTPUTS = 0x0229
MGMSG_RACK_GET_DIGOUTPUTS = 0x0230
MGMSG_MOD_SET_DIGOUTPUTS = 0x0213
MGMSG_MOD_REQ_DIGOUTPUTS = 0x0214
MGMSG_MOD_GET_DIGOUTPUTS = 0x0215
# Message codes for all the motor related messages
MGMSG_HW_YES_FLASH_PROGRAMMING = 0x0017
MGMSG_HW_NO_FLASH_PROGRAMMING = 0x0018
MGMSG_MOT_SET_POSCOUNTER = 0x0410
MGMSG_MOT_REQ_POSCOUNTER = 0x0411
MGMSG_MOT_GET_POSCOUNTER = 0x0412
MGMSG_MOT_SET_ENCCOUNTER = 0x0409
MGMSG_MOT_REQ_ENCCOUNTER = 0x040A
MGMSG_MOT_GET_ENCCOUNTER = 0x040B
MGMSG_MOT_SET_VELPARAMS = 0x0413
MGMSG_MOT_REQ_VELPARAMS = 0x0414
MGMSG_MOT_GET_VELPARAMS = 0x0415
MGMSG_MOT_SET_JOGPARAMS = 0x0416
MGMSG_MOT_REQ_JOGPARAMS = 0x0417
MGMSG_MOT_GET_JOGPARAMS = 0x0418
MGMSG_MOT_REQ_ADCINPUTS = 0x042B
MGMSG_MOT_GET_ADCINPUTS = 0x042C
MGMSG_MOT_SET_POWERPARAMS = 0x0426
MGMSG_MOT_REQ_POWERPARAMS = 0x0427
MGMSG_MOT_GET_POWERPARAMS = 0x0428
MGMSG_MOT_SET_GENMOVEPARAMS = 0x043A
MGMSG_MOT_REQ_GENMOVEPARAMS = 0x043B
MGMSG_MOT_GET_GENMOVEPARAMS = 0x043C
MGMSG_MOT_SET_MOVERELPARAMS = 0x0445
MGMSG_MOT_REQ_MOVERELPARAMS = 0x0446
MGMSG_MOT_GET_MOVERELPARAMS = 0x0447
MGMSG_MOT_SET_MOVEABSPARAMS = 0x0450
MGMSG_MOT_REQ_MOVEABSPARAMS = 0x0451
MGMSG_MOT_GET_MOVEABSPARAMS = 0x0452
MGMSG_MOT_SET_HOMEPARAMS = 0x0440
MGMSG_MOT_REQ_HOMEPARAMS = 0x0441
MGMSG_MOT_GET_HOMEPARAMS = 0x0442
MGMSG_MOT_SET_LIMSWITCHPARAMS = 0x0423
MGMSG_MOT_REQ_LIMSWITCHPARAMS = 0x0424
MGMSG_MOT_GET_LIMSWITCHPARAMS = 0x0425
MGMSG_MOT_MOVE_HOME = 0x0443
MGMSG_MOT_MOVE_HOMED = 0x0444
MGMSG_MOT_MOVE_RELATIVE = 0x0448
MGMSG_MOT_MOVE_COMPLETED = 0x0464
MGMSG_MOT_MOVE_ABSOLUTE = 0x0453
MGMSG_MOT_MOVE_JOG = 0x046A
MGMSG_MOT_MOVE_VELOCITY = 0x0457
MGMSG_MOT_MOVE_STOP = 0x0465
MGMSG_MOT_MOVE_STOPPED = 0x0466
MGMSG_MOT_SET_DCPIDPARAMS = 0x04A0
MGMSG_MOT_REQ_DCPIDPARAMS = 0x04A1
MGMSG_MOT_GET_DCPIDPARAMS = 0x04A2
MGMSG_MOT_SET_AVMODES = 0x04B3
MGMSG_MOT_REQ_AVMODES = 0x04B4
MGMSG_MOT_GET_AVMODES = 0x04B5
MGMSG_MOT_SET_POTPARAMS = 0x04B0
MGMSG_MOT_REQ_POTPARAMS = 0x04B1
MGMSG_MOT_GET_POTPARAMS = 0x04B2
MGMSG_MOT_SET_BUTTONPARAMS = 0x04B6
MGMSG_MOT_REQ_BUTTONPARAMS = 0x04B7
MGMSG_MOT_GET_BUTTONPARAMS = 0x04B8
MGMSG_MOT_SET_EEPROMPARAMS = 0x04B9
MGMSG_MOT_SET_PMDPOSITIONLOOPPARAMS = 0x04D7
MGMSG_MOT_REQ_PMDPOSITIONLOOPPARAMS = 0x04D8
MGMSG_MOT_GET_PMDPOSITIONLOOPPARAMS = 0x04D9
MGMSG_MOT_SET_PMDMOTOROUTPUTPARAMS = 0x04DA
MGMSG_MOT_REQ_PMDMOTOROUTPUTPARAMS = 0x04DB
MGMSG_MOT_GET_PMDMOTOROUTPUTPARAMS = 0x04DC
MGMSG_MOT_SET_PMDTRACKSETTLEPARAMS = 0x04E0
MGMSG_MOT_REQ_PMDTRACKSETTLEPARAMS = 0x04E1
MGMSG_MOT_GET_PMDTRACKSETTLEPARAMS = 0x04E2
MGMSG_MOT_SET_PMDPROFILEMODEPARAMS = 0x04E3
MGMSG_MOT_REQ_PMDPROFILEMODEPARAMS = 0x04E4
MGMSG_MOT_GET_PMDPROFILEMODEPARAMS = 0x04E5
MGMSG_MOT_SET_PMDJOYSTICKPARAMS = 0x04E6
MGMSG_MOT_REQ_PMDJOYSTICKPARAMS = 0x04E7
MGMSG_MOT_GET_PMDJOYSTICKPARAMS = 0x04E8
MGMSG_MOT_SET_PMDCURRENTLOOPPARAMS = 0x04D4
MGMSG_MOT_REQ_PMDCURRENTLOOPPARAMS = 0x04D5
MGMSG_MOT_GET_PMDCURRENTLOOPPARAMS = 0x04D6
MGMSG_MOT_SET_PMDSETTLEDCURRENTLOOPPARAMS = 0x04E9
MGMSG_MOT_REQ_PMDSETTLEDCURRENTLOOPPARAMS = 0x04EA
MGMSG_MOT_GET_PMDSETTLEDCURRENTLOOPPARAMS = 0x04EB
MGMSG_MOT_SET_PMDSTAGEAXISPARAMS = 0x04F0
MGMSG_MOT_REQ_PMDSTAGEAXISPARAMS = 0x04F1
MGMSG_MOT_GET_PMDSTAGEAXISPARAMS = 0x04F2
MGMSG_MOT_GET_STATUSUPDATE = 0x0481
MGMSG_MOT_REQ_STATUSUPDATE = 0x0480
MGMSG_MOT_GET_DCSTATUSUPDATE = 0x0491
MGMSG_MOT_REQ_DCSTATUSUPDATE = 0x0490
MGMSG_MOT_ACK_DCSTATUSUPDATE = 0x0492
MGMSG_MOT_REQ_STATUSBITS = 0x0429
MGMSG_MOT_GET_STATUSBITS = 0x042A
MGMSG_MOT_SUSPEND_ENDOFMOVEMSGS = 0x046B
MGMSG_MOT_RESUME_ENDOFMOVEMSGS = 0x046C
MGMSG_MOT_SET_TRIGGER = 0x0500
MGMSG_MOT_REQ_TRIGGER = 0x0501
MGMSG_MOT_GET_TRIGGER = 0x0502
MGMSG_MOT_SET_TDIPARAMS = 0x04FB
MGMSG_MOT_REQ_TDIPARAMS = 0x04FC
MGMSG_MOT_GET_TDIPARAMS = 0x04FD
# Message codes for all the solenoid related messages
MGMSG_MOT_SET_SOL_OPERATINGMODE = 0x04C0
MGMSG_MOT_REQ_SOL_OPERATINGMODE = 0x04C1
MGMSG_MOT_GET_SOL_OPERATINGMODE = 0x04C2
MGMSG_MOT_SET_SOL_CYCLEPARAMS = 0x04C3
MGMSG_MOT_REQ_SOL_CYCLEPARAMS = 0x04C4
MGMSG_MOT_GET_SOL_CYCLEPARAMS = 0x04C5
MGMSG_MOT_SET_SOL_INTERLOCKMODE = 0x04C6
MGMSG_MOT_REQ_SOL_INTERLOCKMODE = 0x04C7
MGMSG_MOT_GET_SOL_INTERLOCKMODE = 0x04C8
MGMSG_MOT_SET_SOL_STATE = 0x04CB
MGMSG_MOT_REQ_SOL_STATE = 0x04CC
MGMSG_MOT_GET_SOL_STATE = 0x04CD
# Message codes for all the piezo related messages
MGMSG_PZ_SET_POSCONTROLMODE = 0x0640
MGMSG_PZ_REQ_POSCONTROLMODE = 0x0641
MGMSG_PZ_GET_POSCONTROLMODE = 0x0642
MGMSG_PZ_SET_OUTPUTVOLTS = 0x0643
MGMSG_PZ_REQ_OUTPUTVOLTS = 0x0644
MGMSG_PZ_GET_OUTPUTVOLTS = 0x0645
MGMSG_PZ_SET_OUTPUTPOS = 0x0646
MGMSG_PZ_REQ_OUTPUTPOS = 0x0647
MGMSG_PZ_GET_OUTPUTPOS = 0x0648
MGMSG_PZ_SET_INPUTVOLTSSRC = 0x0652
MGMSG_PZ_REQ_INPUTVOLTSSRC = 0x0653
MGMSG_PZ_GET_INPUTVOLTSSRC = 0x0654
MGMSG_PZ_SET_PICONSTS = 0x0655
MGMSG_PZ_REQ_PICONSTS = 0x0656
MGMSG_PZ_GET_PICONSTS = 0x0657
MGMSG_PZ_REQ_PZSTATUSBITS = 0x065B
MGMSG_PZ_GET_PZSTATUSBITS = 0x065C
MGMSG_PZ_GET_PZSTATUSUPDATE = 0x0661
MGMSG_PZ_ACK_PZSTATUSUPDATE = 0x0662
MGMSG_PZ_SET_OUTPUTLUT = 0x0700
MGMSG_PZ_REQ_OUTPUTLUT = 0x0701
MGMSG_PZ_GET_OUTPUTLUT = 0x0702
MGMSG_PZ_SET_OUTPUTLUTPARAMS = 0x0703
MGMSG_PZ_REQ_OUTPUTLUTPARAMS = 0x0704
MGMSG_PZ_GET_OUTPUTLUTPARAMS = 0x0705
MGMSG_PZ_START_LUTOUTPUT = 0x0706
MGMSG_PZ_STOP_LUTOUTPUT = 0x0707
MGMSG_PZ_SET_EEPROMPARAMS = 0x07D0
MGMSG_PZ_SET_TPZ_DISPSETTINGS = 0x07D1
MGMSG_PZ_REQ_TPZ_DISPSETTINGS = 0x07D2
MGMSG_PZ_GET_TPZ_DISPSETTINGS = 0x07D3
MGMSG_PZ_SET_TPZ_IOSETTINGS = 0x07D4
MGMSG_PZ_REQ_TPZ_IOSETTINGS = 0x07D5
MGMSG_PZ_GET_TPZ_IOSETTINGS = 0x07D6
MGMSG_PZ_SET_ZERO = 0x0658
MGMSG_PZ_REQ_MAXTRAVEL = 0x0650
MGMSG_PZ_GET_MAXTRAVEL = 0x0651
MGMSG_PZ_SET_IOSETTINGS = 0x0670
MGMSG_PZ_REQ_IOSETTINGS = 0x0671
MGMSG_PZ_GET_IOSETTINGS = 0x0672
MGMSG_PZ_SET_OUTPUTMAXVOLTS = 0x0680
MGMSG_PZ_REQ_OUTPUTMAXVOLTS = 0x0681
MGMSG_PZ_GET_OUTPUTMAXVOLTS = 0x0682
MGMSG_PZ_SET_TPZ_SLEWRATES = 0x0683
MGMSG_PZ_REQ_TPZ_SLEWRATES = 0x0684
MGMSG_PZ_GET_TPZ_SLEWRATES = 0x0685
MGMSG_MOT_SET_PZSTAGEPARAMDEFAULTS = 0x0686
MGMSG_PZ_SET_LUTVALUETYPE = 0x0708
MGMSG_PZ_SET_TSG_IOSETTINGS = 0x07DA
MGMSG_PZ_REQ_TSG_IOSETTINGS = 0x07DB
MGMSG_PZ_GET_TSG_IOSETTINGS = 0x07DC
MGMSG_PZ_REQ_TSG_READING = 0x07DD
MGMSG_PZ_GET_TSG_READING = 0x07DE
# Message codes for all the NanoTrak related messages
MGMSG_PZ_SET_NTMODE = 0x0603
MGMSG_PZ_REQ_NTMODE = 0x0604
MGMSG_PZ_GET_NTMODE = 0x0605
MGMSG_PZ_SET_NTTRACKTHRESHOLD = 0x0606
MGMSG_PZ_REQ_NTTRACKTHRESHOLD = 0x0607
MGMSG_PZ_GET_NTTRACKTHRESHOLD = 0x0608
MGMSG_PZ_SET_NTCIRCHOMEPOS = 0x0609
MGMSG_PZ_REQ_NTCIRCHOMEPOS = 0x0610
MGMSG_PZ_GET_NTCIRCHOMEPOS = 0x0611
MGMSG_PZ_MOVE_NTCIRCTOHOMEPOS = 0x0612
MGMSG_PZ_REQ_NTCIRCCENTREPOS = 0x0613
MGMSG_PZ_GET_NTCIRCCENTREPOS = 0x0614
MGMSG_PZ_SET_NTCIRCPARAMS = 0x0618
MGMSG_PZ_REQ_NTCIRCPARAMS = 0x0619
MGMSG_PZ_GET_NTCIRCPARAMS = 0x0620
MGMSG_PZ_SET_NTCIRCDIA = 0x061A
MGMSG_PZ_SET_NTCIRCDIALUT = 0x0621
MGMSG_PZ_REQ_NTCIRCDIALUT = 0x0622
MGMSG_PZ_GET_NTCIRCDIALUT = 0x0623
MGMSG_PZ_SET_NTPHASECOMPPARAMS = 0x0626
MGMSG_PZ_REQ_NTPHASECOMPPARAMS = 0x0627
MGMSG_PZ_GET_NTPHASECOMPPARAMS = 0x0628
MGMSG_PZ_SET_NTTIARANGEPARAMS = 0x0630
MGMSG_PZ_REQ_NTTIARANGEPARAMS = 0x0631
MGMSG_PZ_GET_NTTIARANGEPARAMS = 0x0632
MGMSG_PZ_SET_NTGAINPARAMS = 0x0633
MGMSG_PZ_REQ_NTGAINPARAMS = 0x0634
MGMSG_PZ_GET_NTGAINPARAMS = 0x0635
MGMSG_PZ_SET_NTTIALPFILTERPARAMS = 0x0636
MGMSG_PZ_REQ_NTTIALPFILTERPARAMS = 0x0637
MGMSG_PZ_GET_NTTIALPFILTERPARAMS = 0x0638
MGMSG_PZ_REQ_NTTIAREADING = 0x0639
MGMSG_PZ_GET_NTTIAREADING = 0x063A
MGMSG_PZ_SET_NTFEEDBACKSRC = 0x063B
MGMSG_PZ_REQ_NTFEEDBACKSRC = 0x063C
MGMSG_PZ_GET_NTFEEDBACKSRC = 0x063D
MGMSG_PZ_REQ_NTSTATUSBITS = 0x063E
MGMSG_PZ_GET_NTSTATUSBITS = 0x063F
MGMSG_PZ_REQ_NTSTATUSUPDATE = 0x0664
MGMSG_PZ_GET_NTSTATUSUPDATE = 0x0665
MGMSG_PZ_ACK_NTSTATUSUPDATE = 0x0666
MGMSG_NT_SET_EEPROMPARAMS = 0x07E7
MGMSG_NT_SET_TNA_DISPSETTINGS = 0x07E8
MGMSG_NT_REQ_TNA_DISPSETTINGS = 0x07E
MGMSG_NT_GET_TNA_DISPSETTINGS = 0x07EA
MGMSG_NT_SET_TNAIOSETTINGS = 0x07EB
MGMSG_NT_REQ_TNAIOSETTINGS = 0x07EC
MGMSG_NT_GET_TNAIOSETTINGS = 0x07ED
# Message codes for all the laser related messages
MGMSG_LA_SET_PARAMS = 0x0800
MGMSG_LA_REQ_PARAMS = 0x0801
MGMSG_LA_GET_PARAMS = 0x0802
MGMSG_LA_ENABLEOUTPUT = 0x0811
MGMSG_LA_DISABLEOUTPUT = 0x0812
MGMSG_LA_REQ_STATUSUPDATE = 0x0820
MGMSG_LA_GET_STATUSUPDATE = 0x0821
MGMSG_LA_ACK_STATUSUPDATE = 0x0822
# Message codes for all the Quad control related messages
MGMSG_QUAD_SET_PARAMS = 0x0870
MGMSG_QUAD_REQ_PARAMS = 0x0871
MGMSG_QUAD_GET_PARAMS = 0x0872
MGMSG_QUAD_REQ_STATUSUPDATE = 0x0880
MGMSG_QUAD_GET_STATUSUPDATE = 0x0881
MGMSG_QUAD_SET_EEPROMPARAMS = 0x087

# Actually implemented in the first section of code
"""
# Generic Commands
MGMSG_MOD_IDENTIFY = 0x0223
MGMSG_HW_RESPONSE = 0x0080

MGMSG_HW_REQ_INFO = 0x0005
MGMSG_HW_GET_INFO = 0x0006

MGMSG_MOT_ACK_DCSTATUSUPDATE = 0x0492

# Motor Commands
MGMSG_MOT_SET_PZSTAGEPARAMDEFAULTS = 0x0686

MGMSG_MOT_MOVE_HOME = 0x0443
MGMSG_MOT_MOVE_HOMED = 0x0444
MGMSG_MOT_MOVE_ABSOLUTE = 0x0453
MGMSG_MOT_MOVE_COMPLETED = 0x0464

MGMSG_MOT_SET_HOMEPARAMS = 0x0440
MGMSG_MOT_REQ_HOMEPARAMS = 0x0441
MGMSG_MOT_GET_HOMEPARAMS = 0x0442

MGMSG_MOT_REQ_POSCOUNTER = 0x0411
MGMSG_MOT_GET_POSCOUNTER = 0x0412

MGMSG_MOT_REQ_DCSTATUSUPDATE = 0x0490
MGMSG_MOT_GET_DCSTATUSUPDATE = 0x0491

MGMSG_MOT_SET_VELPARAMS = 0x413
MGMSG_MOT_REQ_VELPARAMS = 0x414
MGMSG_MOT_GET_VELPARAMS = 0x415

MGMSG_MOT_SUSPEND_ENDOFMOVEMSGS = 0x046B
MGMSG_MOT_RESUME_ENDOFMOVEMSGS = 0x046C

MGMSG_MOT_MOVE_STOP = 0x0465
MGMSG_MOT_MOVE_STOPPED = 0x0466
"""
