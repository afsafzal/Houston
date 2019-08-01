from typing import Type, Dict, Callable, Optional, Any
import logging
import attr
import re

from .base import MissionGenerator
from ..mission import Mission
from ..system import System
from ..state import State
from ..environment import Environment
from ..configuration import Configuration
from ..command import Command
from ..exceptions import HoustonException

logger = logging.getLogger(__name__)   # type: logging.Logger
logger.setLevel(logging.DEBUG)


class FailedMissionGenerationException(HoustonException):
    """
    Thrown whenever the mission generation fails to follow the
    template.
    """


@attr.s
class CommandTemplate:
    """
    A CommandTemplate describes template for a set of commands.
    """

    cmd = attr.ib(type=str)
    repeats = attr.ib(type=int)
    params = attr.ib(type=Optional[Dict[str, Any]], default=None)

    @staticmethod
    def from_str(template_str: str) -> 'CommandTemplate':
        """
        Creates a CommandTemplate based on provided template
        string. The template should take the following format:
            `<COMMAND NAME>(<FIXED PARAMETERS>)^<NUMBER OF REPEATS>`
        Example:
            `TAKEOFF(alt: 10.3)^2` which means template is for
            two `TAKEOFF` commands with parameter `alt` set to 10.3
        Providing the parameters and number of repeats are
        optional. By default, number of repeats is set to 1. If `*`
        is provided as number of repeates, it will be dynamically
        decided. If command name is provided as `.` it means any
        possible command.
        """

        regex = r"(?P<cmd>[a-zA-Z\.\_]+)(?P<params>\(.*\))?(?P<repeats>\^[\d\*]*)?"  # noqa: pycodestyle
        matched = re.fullmatch(regex, template_str.strip())
        if not matched:
            logger.error("Template is wrong %s", template_str)
            return None
        groups = matched.groupdict()
        cmd = groups['cmd']
        params = None
        repeats = 1
        if groups['params']:
            pairs = groups['params'].strip()[1:-1].split(",")
            params = {}
            for pair in pairs:
                splited = pair.split(":")
                assert len(splited) == 2
                params[splited[0].strip()] = eval(splited[1])
        if groups['repeats']:
            r = groups['repeats'][1:].strip()
            if r == '*':
                repeats = -1
            else:
                repeats = int(r)
        return CommandTemplate(cmd, repeats, params)

    def __str__(self):
        s = "cmd: {}, params:{}, repeats: {}"
        return s.format(self.cmd,
                        self.params,
                        self.repeats)


class TemplateBasedMissionGenerator(MissionGenerator):
    """
    Given a template for intended missions, this generator
    generates missions.
    """

    def __init__(self,
                 system: Type[System],
                 initial_state: State,
                 env: Environment,
                 config: Configuration,
                 threads: int = 1,
                 command_generators: Optional[Dict[str, Callable]] = None,
                 max_num_commands: int = 10
                 ) -> None:
        super().__init__(system, threads, command_generators, max_num_commands)
        self.__initial_state = initial_state
        self.__env = env
        self.__configuration = config

    @property
    def initial_state(self):
        """
        The initial state used by all missions produced by this generator.
        """
        return self.__initial_state

    @property
    def env(self):
        """
        The environment used by all missions produced by this generator.
        """
        return self.__env

    def generate_command(self,
                         command_class: Type[Command],
                         params: Dict[str, Any]
                         ) -> Command:
        generator = self.command_generator(command_class)
        if generator is None:
            return command_class.generate_fixed_params(params,
                                                       self.rng)
        # g = generator.generate_action_without_state
        # return g(self.system, self.__env, self.rng)
        return g(self.rng)

    def generate_mission(self, template: str):
        """
        A list of CommandTemplate strings separated by `-`
        should be provided as template.
        Example:
            TAKEOFF(alt: 10.3)-.^*-LAND-.^1

        raises:
            FailedMissionGenerationException:
                It failed to generate a mission for this
                template.
        """
        command_templates = [CommandTemplate.from_str(t)
                             for t in template.split("-")]
        cmds_len = self.max_num_commands
        cmds_len -= sum([c.repeats for c in command_templates
                         if c.repeats > 0])
        command_classes = list(self.system.commands.values())
        for tries in range(50):
            # try at most 50 times to generate a mission
            commands = []
            max_nonfixed_commands = cmds_len
            try:
                for ct in command_templates:
                    r = ct.repeats
                    if r <= 0:
                        # number of repeats between 0 and max allowed
                        r = self.rng.randint(0, max_nonfixed_commands)
                    for _ in range(r):
                        if commands:
                            next_allowed = commands[-1].__class__.get_next_allowed(self.system)  # noqa: pycodestyle
                        else:
                            # everything is allowed
                            next_allowed = [cc for cc in command_classes]

                        if ct.cmd != '.':
                            next_allowed = [cc for cc in next_allowed
                                            if ct.cmd in cc.uid]

                        if not next_allowed:
                            if ct.repeats > 0:
                                # logger.debug("So far %s", commands)
                                commands = []
                                raise FailedMissionGenerationException
                            else:
                                break
                        params = ct.params or {}
                        command_class = self.rng.choice(next_allowed)
                        commands.append(self.generate_command(command_class,
                                                              params))
                        if ct.repeats <= 0:
                            max_nonfixed_commands -= 1
                break
            except FailedMissionGenerationException:
                logger.debug("Try %d failed", tries)
                continue
        if not commands:
            raise FailedMissionGenerationException("Mission generation failed")
        logger.debug("Generated mission: %s", commands)
        return Mission(self.__configuration,
                       self.__env,
                       self.__initial_state,
                       commands,
                       self.system)
