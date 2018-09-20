__all__ = ['GotoLoiter', 'ArmDisarm']

import time

import geopy
import geopy.distance
from pymavlink import mavutil

from .sandbox import Sandbox
from ..state import State
from ..environment import Environment
from ..valueRange import ContinuousValueRange, DiscreteValueRange
from ..configuration import Configuration
from ..command import Parameter, Command
from ..specification import Specification, Idle


class ArmNormally(Specification):
    def __init__(self) -> None:
        super().__init__('arm-normal',
		"""
                (and (= $arm true)
                    (= _armable true)
                    (or (= _mode "GUIDED") (= _mode "LOITER")))
                """,
                """
                (= __armed true)
                """)


class DisarmNormally(Specification):
    def __init__(self) -> None:
        super().__init__('disarm-normal', 
		"""
                (and (= $arm false)
                    (= _armed true))
                """,
                """
                (= __armed false)
                """)


class GotoLoiter(Specification):
    """
    If the robot is armed and in its `LOITER` mode, GoTo actions should have no
    effect upon the robot. (Why isn't this covered by Idle?)
    """
    def __init__(self) -> None:

        super().__init__('loiter',
	"""
        (and (= _armed true)
            (= _mode "LOITER"))
        """,
        """
        (and (= __longitude $longitude)
            (= __latitude $latitude)
            (= __altitude $altitude)
            (= __mode "LOITER"))
        """)


class ArmDisarm(Command):
    """
    Behaviours:
        Normal: if the robot is armable and is in either its 'GUIDED' or
            'LOITER' modes, the robot will become armed.
        Idle: if the conditions above cannot be met, the robot will ignore the
            command.
    """
    name = 'arm'
    parameters = [
        Parameter('arm', DiscreteValueRange([True, False]))
    ]
    specifications = [
        ArmNormally(),
        DisarmNormally(),
        Idle()
    ]

    def dispatch(self,
                 sandbox: Sandbox,
                 state: State,
                 environment: Environment,
                 configuration: Configuration
                 ) -> None:
        vehicle = sandbox.connection
        arm_flag = 1 if self.arm else 0
        msg = vehicle.message_factory.command_long_encode(
            0, 0,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, arm_flag, 0, 0, 0, 0, 0, 0)
        vehicle.send_mavlink(msg)