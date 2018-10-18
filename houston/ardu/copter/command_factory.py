import os
import logging
import yaml
from typing import Dict, Any, Type

from ..connection import CommandLong
from ...valueRange import ContinuousValueRange, DiscreteValueRange
from ...command import Parameter, Command, CommandMeta
from ...specification import Idle 

logger = logging.getLogger(__name__)  # type: logging.Logger
logger.setLevel(logging.DEBUG)

def create_command(command: Dict[str, Any]) -> Type[Command]:
    name = command['name']
    id = command['id']
    parameters = []
    params_name = {}
    for i in range(1,8):
        p = 'p{}'.format(i)
        if p in command:
            param = None
            p_name = command[p]['name']
            if command[p]['value']['type'] == 'discrete':
                vals = command[p]['value']['vals']
                param = Parameter(p_name, DiscreteValueRange(vals))
            elif command[p]['value']['type'] == 'continous':
                min_value = command[p]['value']['min']
                max_value = command[p]['value']['max']
                param = Parameter(p_name, ContinuousValueRange(min_value, max_value, True))
            else:
                logger.error("The type of value not supported")
                raise Exception
            parameters.append(param)
            params_name['param_{}'.format(i)] = p_name
        else:
            params_name['param_{}'.format(i)] = 0

    def to_message(self):
        params = {}
        for p, n in params_name.items():
            if not n:
                params[p] = n
            else:
                params[p] = self[n]
        return CommandLong(0, 0, id, **params)

    ns = {'name': name,
          'to_message': to_message,
          'parameters': parameters,
          'specifications': [Idle]}

    C = CommandMeta(name, (Command,), ns)

    logger.info("Command class generated: %s", C)
    return C

def read_commands_yml():
    all_commands = []
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'commands.yml')
    with open(filename, 'r') as f:
        all_commands = yaml.load(f)['commands']
    classes = []
    for command in all_commands:
        command_class = create_command(command)
        classes.append(command_class)
    return classes

