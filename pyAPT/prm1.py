from __future__ import absolute_import, division
from .controller import Controller

class PRM1(Controller):
  """
  A controller for a PRM1 rotation stage
  """
  def __init__(self,*args, **kwargs):
    super(PRM1, self).__init__(*args, **kwargs)

    """ Initialization sequence for the PRM1 from the Thorlabs ActiveX controls
    MGMSG_MOD_SET_CHANENABLESTATE -> 10,02,01,01,50,01
    MGMSG_MOT_SET_VELPARAMS -> 13,04,0E,00,D0,01,01,00,00,00,00,00,93,00,00,00,5F,8D,06,00
    MGMSG_MOT_SET_JOGPARAMS -> 16,04,16,00,D0,01,01,00,02,00,7E,25,00,00,BD,08,00,00,DC,00,00,00,25,D4,09,00,02,00
    MGMSG_MOT_SET_LIMSWITCHPARAMS -> 23,04,10,00,D0,01,01,00,04,00,01,00,80,07,00,00,80,07,00,00,01,00
    MGMSG_MOT_SET_GENMOVEPARAMS -> 3A,04,06,00,D0,01,01,00,80,07,00,00
    MGMSG_MOT_SET_HOMEPARAMS -> 40,04,0E,00,D0,01,01,00,02,00,01,00,5F,8D,06,00,FF,1D,00,00
    MGMSG_MOT_SET_MOVERELPARAMS -> 45,04,06,00,D0,01,01,00,00,0A,00,00
    MGMSG_MOT_SET_MOVEABSPARAMS -> 50,04,06,00,D0,01,01,00,00,00,00,00
    MGMSG_MOT_SET_DCPIDPARAMS -> A0,04,14,00,D0,01,01,00,52,03,00,00,96,00,00,00,A0,0A,00,00,32,00,00,00,0F,00
    MGMSG_MOT_SET_AVMODES -> B3,04,04,00,D0,01,01,00,0F,00
    MGMSG_MOT_SET_BUTTONPARAMS -> B6,04,10,00,D0,01,01,00,01,00,FC,4A,00,00,F9,95,00,00,D0,07,D0,07
    MGMSG_MOT_SET_POTPARAMS -> B0,04,1A,00,D0,01,01,00,14,00,BE,A7,00,00,32,00,B4,46,03,00,50,00,69,8D,06,00,64,00,D1,1A,0D,00
    """

    # http://www.thorlabs.de/newgrouppage9.cfm?objectgroup_id=2875
    # Note that these values should be pulled from the APT User software,
    # as they agree with the real limits of the stage better than
    # what the website or the user manual states
    #self.max_velocity = 0.3 # units?
    #self.max_acceleration = 0.3 # units?

    # from the manual
    # encoder counts per revoultion of the output shaft: 34304
    # no load speed: 16500 rpm = 275 1/s
    # max rotation velocity: 25deg/s
    # Gear ratio: 274 / 25 rounds/deg
    # to move 1 deg: 274/25 rounds = 274/25 * 34304 encoder steps
    # measured value: 1919.2689
    # There is an offset off 88.2deg -> enc(0) = 88.2deg
    #enccnt = 1919.2698

    # use the EncCnt value from the thorlabs documentation
    enccnt = 1919.64

    T = 2048/6e6

    # these equations are taken from the APT protocol manual
    self.position_scale = enccnt  #the number of enccounts per deg
    self.velocity_scale = enccnt * T * 65536
    self.acceleration_scale = enccnt * T * T * 65536

    #self.linear_range = (-180,180)
    #self.linear_range = (-float('Inf'),float('Inf'))
    self.linear_range = (0,360)

    # velocity initialization parameters (encoder counts)
    self.max_vel_apt = 0x068d5f
    self.accel = 0x08bd

    # jog initialization parameters (encoder counts)
    self.jog_mode = 0x02
    self.jog_step = 0x257e
    self.jog_max_vel = 0x09d425
    self.jog_accel = 0xdc
    # this value must be zero according to the APT manual
    #self.jog_min_vel = 0x08bd
