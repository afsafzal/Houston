import statistics
import rospy
import time
import numpy
import os
import subprocess as sub
import sys
import pexpect
from pymavlink import mavutil, mavwp
from geopy             import distance
from dronekit_sitl     import SITL
from dronekit          import connect, VehicleMode, LocationGlobalRelative
from system            import System, InternalStateVariable, ActionSchema, Predicate, \
                              Invariant, Postcondition, Precondition, Parameter
testdir = os.path.abspath("/home/robot/ardupilot/Tools/autotest")
sys.path.append(testdir)

from common import expect_callback, expect_list_clear, expect_list_extend, message_hook, idle_hook
from pysim import util, vehicleinfo
SAMPLE_BATTERY = []
SAMPLE_TIME    = []
WINDOW_BATTERY = .025
WINDOW_TIME    = 2

vinfo = vehicleinfo.VehicleInfo()

"""
Description of the ArduPilot system
"""
class ArduPilot(System):

    def __init__(self):
        # TOOD: rename!
        self.system = None
        self._temp_sitl = None
        self._temp_mavproxy = None
        #self._temp_sitl    = None

        variables = {}
        variables['time'] = InternalStateVariable('time', lambda: time.time())
        variables['altitude'] = InternalStateVariable('altitude',
            lambda: self.system.location.global_relative_frame.alt)
        variables['latitude'] = InternalStateVariable('latitude',
            lambda: self.system.location.global_relative_frame.lat)
        variables['longitude'] = InternalStateVariable('longitude',
            lambda: self.system.location.global_relative_frame.lon)
        variables['battery'] = InternalStateVariable('battery',
            lambda: self.system.battery.level)
        variables['armable'] = InternalStateVariable('armable',
            lambda: self.system.is_armable)
        variables['armed'] = InternalStateVariable('armed',
            lambda: self.system.armed)
        variables['mode'] = InternalStateVariable('mode',
            lambda : self.system.mode.name)
        schemas = {
            'goto'   : GoToActionSchema(),
            'takeoff': TakeoffActionSchema(),
            'land'   : LandActionSchema(),
            'arm'    : ArmActionSchema(),
            'setmode'   : SetModeActionSchema()
        }
        super(ArduPilot, self).__init__(variables, schemas)


    def setUp(self, mission):
        ardu_location = '/home/robot/ardupilot'
        binary = os.path.join(ardu_location, 'build/sitl/bin/arducopter')
        param_file = os.path.join(ardu_location, 'Tools/autotest/default_params/copter.parm')

        sitl = util.start_SITL(binary, wipe=True, model='quad', home='-35.362938, 149.165085, 584, 270', speedup=5)
        mavproxy = util.start_MAVProxy_SITL('ArduCopter', options='--sitl=127.0.0.1:5501 --out=127.0.0.1:19550 --quadcopter')
        mavproxy.expect('Received [0-9]+ parameters')

        # setup test parameters
        params = vinfo.options["ArduCopter"]["frames"]['quad']["default_params_filename"]
        if not isinstance(params, list):
            params = [params]
            for x in params:
                mavproxy.send("param load %s\n" % os.path.join(testdir, x))

        mavproxy.expect('Loaded [0-9]+ parameters')
        mavproxy.send("param set LOG_REPLAY 1\n")
        mavproxy.send("param set LOG_DISARMED 1\n")
        time.sleep(2)

        # reboot with new parameters
        util.pexpect_close(mavproxy)
        util.pexpect_close(sitl)

        self._temp_sitl = util.start_SITL(binary, model='quad', home='-35.362938, 149.165085, 584, 270', speedup=5, valgrind=False, gdb=False)
        options = '--sitl=127.0.0.1:5501 --out=127.0.0.1:19550 --out=127.0.0.1:14551 --quadcopter --streamrate=5'
        self._temp_mavproxy = util.start_MAVProxy_SITL('ArduCopter', options=options)
        self._temp_mavproxy.expect('Telemetry log: (\S+)')
        logfile = self._temp_mavproxy.match.group(1)
        print("LOGFILE %s" % logfile)

        # the received parameters can come before or after the ready to fly message
        self._temp_mavproxy.expect(['Received [0-9]+ parameters', 'Ready to FLY'])
        self._temp_mavproxy.expect(['Received [0-9]+ parameters', 'Ready to FLY'])

        util.expect_setup_callback(self._temp_mavproxy, expect_callback)

        expect_list_clear()
        expect_list_extend([sitl, self._temp_mavproxy])
        # get a mavlink connection going
        try:
            mav = mavutil.mavlink_connection('127.0.0.1:19550', robust_parsing=True)
        except Exception as msg:
            print("Failed to start mavlink connection on 127.0.0.1:19550 {}".format(msg))
            raise
        mav.message_hooks.append(message_hook)
        mav.idle_hooks.append(idle_hook)

        try:
            mav.wait_heartbeat()
            """Setup RC override control."""
            for chan in range(1, 9):
                self._temp_mavproxy.send('rc %u 1500\n' % chan)
            # zero throttle
            self._temp_mavproxy.send('rc 3 1000\n')
            self._temp_mavproxy.expect('IMU0 is using GPS')
            self.system = connect('127.0.0.1:14551', wait_ready=True)
        except pexpect.TIMEOUT:
            print("Failed: time out")
            return False

    def tearDown(self, mission):
        pass


"""
A description of arm
"""
class ArmActionSchema(ActionSchema):
    """docstring for ArmActionSchema."""
    def __init__(self):
        parameters = []
        preconditions = [
            Precondition('armed', 'description',
                         lambda sv, params: sv['armed'].read() == False),
            Precondition('armable', 'description',
                         lambda sv, params: sv['armable'].read() == True)
        ]
        postconditions = [
            Postcondition('armed', 'description',
                         lambda sv, params: sv['armed'].read() == True)
        ]
        invariants = [
            Invariant('battery', 'description',
                      lambda sv, params: sv['battery'].read() > 0)
        ]
        super(ArmActionSchema, self).__init__('arm', parameters, preconditions, invariants, postconditions)

    def dispatch(self, parameters):
        safe_command_conection('armed = True')


"""
A description of set mode
"""
class SetModeActionSchema(ActionSchema):
    """docstring for SetModeActionSchema"""
    def __init__(self):
        parameters = [
            Parameter('mode', str, 'description')
        ]

        preconditions = [
        ]

        postconditions = [
            Postcondition('mode', 'description',
                          lambda sv, params: sv['mode'].read() == params['mode'])
        ]
        invariants = [
            Invariant('battery', 'description',
                      lambda sv, params: sv['battery'].read() > 0)
        ]
        super(SetModeActionSchema, self).__init__('setmode', parameters, preconditions, invariants, postconditions)

    def dispatch(self, parameters):
        safe_command_conection('mode = VehicleMode(\'{}\')'.format(parameters['mode']))


"""
A description of goto
"""
class GoToActionSchema(ActionSchema):
    def __init__(self):
        parameters = [
            Parameter('latitude', float, 'description'),
            Parameter('longitude', float, 'description'),
            Parameter('altitude', float, 'description')
        ]

        preconditions = [

            Precondition('battery', 'description',
                         lambda sv, params: sv['battery'].read() >= max_expected_battery_usage(
                         params['latitude'],
                         params['longitude'],
                         params['altitude'])),
            Precondition('altitude', 'description',
                         lambda sv, params: sv['altitude'].read() > .3)
        ]

        invariants = [
            Invariant('battery', 'description',
                       lambda sv, params: sv['battery'].read() > 0),
            Invariant('system_armed', 'description',
                       lambda sv, params: sv['armed'].read() == True),
            Invariant('altitude', 'description',
                       lambda sv, params: sv['altitude'].read() > -0.3)
        ]

        postconditions = [
            Postcondition('altitude', 'description',
                          lambda sv, params: sv['altitude'].read() - 0.3 < \
                            params['altitude'] < sv['altitude'].read() + 0.3),
            Postcondition('battery', 'description',
                          lambda sv, params: sv['battery'].read() > 0 ),
            Postcondition('distance', 'description',
                          lambda sv, params:
                          float(distance.great_circle(
                          (float(params['latitude']), float(params['longitude'])),
                          (float(sv['latitude'].read()), float(sv['longitude'].read())))
                          .meters) < 0.5)

        ]

        super(GoToActionSchema, self).__init__('goto',parameters, preconditions, invariants, postconditions)


    def dispatch(self, parameters):
        safe_command_conection('simple_goto(LocationGlobalRelative({},{},{}))'.format(
            parameters['latitude'],
            parameters['longitude'],
            parameters['altitude']))


"""
A description of land
"""
class LandActionSchema(ActionSchema):
    def __init__(self):
        preconditions = [
            Precondition('battery', 'description',
                lambda sv, params: sv['battery'].read() >= \
                    max_expected_battery_usage(None, None, 0)),
            Precondition('altitude', 'description',
                lambda sv, params: sv['altitude'].read() > 0.3),
            Precondition('armed', 'description',
                lambda sv, params: sv['armed'].read() == True)
        ]
        invariants = [
            Invariant('battery', 'description',
                       lambda sv, params: sv['battery'].read() > 0),
            Invariant('altitude', 'description',
                       lambda sv, params: sv['altitude'].read() > -0.3)
        ]
        postconditions = [
            Postcondition('altitude', 'description',
                          lambda sv, params: sv['altitude'].read() < 1 ),
            Postcondition('battery', 'description',
                          lambda sv, params: sv['battery'].read() > 0 ),
            Postcondition('time', 'description',
                          # we need a "start" time (or an initial state)
                          lambda sv, params: max_expected_time(None, None, 0) > \
                            time.time() - sv['time'].read())
        ]
        super(LandActionSchema, self).__init__('land', None, preconditions, invariants, postconditions)


    def dispatch(self, parameters):
        safe_command_conection('mode = VehicleMode(\'LAND\')')


"""
A description of takeoff
"""
class TakeoffActionSchema(ActionSchema):
    """docstring for TakeoffActionSchema."""
    def __init__(self):
        parameters = [
            Parameter('altitude', float, 'description')
        ]
        preconditions = [
            Precondition('battery', 'description',
                         lambda sv, params: sv['battery'].read() >= \
                         max_expected_battery_usage(
                            None,
                            None,
                            sv['battery'].read())),
            Precondition('altitude', 'description',
                         lambda sv, params: sv['altitude'].read() < 1),
            Precondition('armed', 'description',
                         lambda sv, params: sv['armed'].read() == True)
        ]
        invariants = [
            Invariant('armed', 'description',
                      lambda sv, params: sv['armed'].read() == True),
            Invariant('altitude', 'description',
                      lambda sv, params: sv['altitude'].read() > -0.3)
        ]
        postconditions = [
            Postcondition('altitude', 'description',
                          lambda sv, params: sv['altitude'].read() - 1 < \
                          params['altitude'] < sv['altitude'].read() + 1)
        ]
        super(TakeoffActionSchema, self).__init__('takeoff', None, preconditions, invariants, postconditions)

    def dispatch(self, parameters):
      safe_command_conection('simple_takeoff({})'.format(parameters['altitude']))


def safe_command_conection(value):
    system = connect('127.0.0.1:14551', wait_ready=True)
    exec('system.{}'.format(value))
    system.close()



def max_expected_battery_usage(prime_latitude, prime_longitude, prime_altitude):
    return 0.01
    distance = distance.great_circle((0['latitude'], \
        system_variables['longitude']), (prime_latitude, prime_longitude))
    standard_dev, mean  = get_standard_deviation_and_mean(SAMPLE_BATTERY)
    #return (mean + standard_dev + WINDOW_BATTERY) * distance



def max_expected_time(prime_latitude, prime_longitude, prime_altitude):
    return 10
    distance = distance.great_circle((system_variables['latitude'], \
        system_variables['longitude']), (prime_latitude, prime_longitude))
    standard_dev, mean  = get_standard_deviation_and_mean(SAMPLE_TIME)
    #return (mean + standard_dev + WINDOW_BATTERY) * distance


def get_standard_deviation_and_mean(sample):
    return statistics.stdev(sample), numpy.mean(sample)
