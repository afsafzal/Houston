from ..connection import CommandLong
from ...valueRange import ContinuousValueRange, DiscreteValueRange
from ...command import Parameter, Command, CommandMeta
from ...specification import Idle 


def create_command():
    name = 'MAV_CMD_NAV_WAYPOINT'
    id = 16
    p1 = Parameter('delay', ContinuousValueRange(0.0, 10.0, True))
    p5 = Parameter('latitude', ContinuousValueRange(-90.0, 90.0, True))
    p6 = Parameter('longitude', ContinuousValueRange(-180.0, 180.0, True))
    p7 = Parameter('altitude', ContinuousValueRange(0.3, 100.0))

    def to_message(self):
        return CommandLong(0, 0, id, param_1=p1,
                        param_5=p5, param_6=p6, param_7=p7)

    ns = {'name': name,
          'to_message': to_message,
          'parameters': [p1, p5, p6, p7],
          'specifications': [Idle]}

    C = CommandMeta(name, (), ns)

    print(C)
    return C
