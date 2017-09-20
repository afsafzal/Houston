import time

# schemas
import arm
import goto
import setmode
import takeoff

from houston.util import printflush
from houston.ardu.base import BaseSystem
from houston.system import System

try:
    import dronekit
except ImportError:
    pass


class ArduCopter(BaseSystem):
    """
    Description of the ArduCopter system
    """
    @staticmethod
    def from_json(jsn):
        assert isinstance(jsn, dict)
        assert ('settings' in jsn)
        settings = jsn['settings']
        speedup = settings['speedup']
        return ArduCopter(speedup=speedup)


    def __init__(self, speedup=3.0):
        assert isinstance(speedup, float)
        assert (speedup != 0.0)

        # variables specific to the ArduCopter system
        variables = []
        schemas = [
            goto.GoToSchema(),
            takeoff.TakeoffSchema(),
            arm.ArmSchema(),
            setmode.SetModeSchema()
        ]

        super(ArduCopter, self).__init__(variables, schemas, speedup=speedup)

    
    def setup(self, mission):
        super(ArduCopter, self).setup(mission)

        vehicle = self.vehicle
        vehicle_mode = dronekit.VehicleMode('GUIDED')
        vehicle.mode = vehicle_mode
        vehicle.parameters['DISARM_DELAY'] = 0
        vehicle.parameters['RTL_ALT'] = 0

        while vehicle.parameters['DISARM_DELAY'] != 0 and not vehicle.is_armable: #TODO Implement timeout
            time.sleep(0.1)
            vehicle.mode = vehicle_mode
            vehicle.parameters['DISARM_DELAY'] = 0
            vehicle.parameters['RTL_ALT'] = 0


# Register the ArduCopter system type
System.register('arducopter', ArduCopter)
