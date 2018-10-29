from typing import Set, Optional, Tuple, Dict, Sequence, Iterator, Union
from timeit import default_timer as timer
from contextlib import contextmanager
import math
import time
import threading
import signal
import logging

import bugzoo
from bugzoo import Bug as Snapshot
from bugzoo.client import Client as BugZooClient
from bugzoo.core.container import Container
from bugzoo.core.fileline import FileLineSet

from .connection import Message
from .environment import Environment
from .configuration import Configuration
from .state import State
from .command import Command, CommandOutcome
from .recorder import Recorder

logger = logging.getLogger(__name__)  # type: logging.Logger
logger.setLevel(logging.DEBUG)


class Sandbox(object):
    """
    Sandboxes are used to provide an isolated, idempotent environment for
    executing test cases on a given system.
    """
    @classmethod
    @contextmanager
    def for_snapshot(cls,
                     client_bugzoo: BugZooClient,
                     snapshot_or_name: Union[str, Snapshot],
                     state_initial: State,
                     environment: Environment,
                     configuration: Configuration
                     ) -> Iterator['Sandbox']:
        """
        Creates an ephemeral BugZoo container using a provided image before
        launching an interactive sandbox instance inside that container. The
        Docker container (and all of its associated resources) is automatically
        created and destroyed upon entering and leaving the context.
        """
        if isinstance(snapshot_or_name, str):
            snapshot = client_bugzoo.bugs[snapshot_or_name]
        else:
            snapshot = snapshot_or_name

        container = None  # type: Optional[Container]
        try:
            container = client_bugzoo.containers.provision(snapshot)
            with cls.for_container(client_bugzoo, container, state_initial, environment, configuration) as sandbox:  # noqa: pycodestyle
                yield sandbox
        finally:
            if container:
                del client_bugzoo.containers[container.uid]

    @classmethod
    @contextmanager
    def for_container(cls,
                      client_bugzoo: BugZooClient,
                      container: Container,
                      state_initial: State,
                      environment: Environment,
                      configuration: Configuration
                      ) -> Iterator['Sandbox']:
        """
        Launches an interactive sandbox instance within a given Docker
        container. The sandbox instance within the container is automatically
        started and stopped upon entering and leaving its context.
        """
        sandbox = cls(client_bugzoo,
                      container,
                      state_initial,
                      environment,
                      configuration)
        try:
            sandbox.start()
            yield sandbox
        finally:
            sandbox.stop()

    def __init__(self,
                 client_bugzoo: BugZooClient,
                 container: Container,
                 state_initial: State,
                 environment: Environment,
                 configuration: Configuration,
                 ) -> None:
        self.__lock = threading.Lock()
        self.__state_lock = threading.Lock()
        self._bugzoo = client_bugzoo
        self.__container = container
        self.__state = state_initial
        self.__state_initial = state_initial
        self.__environment = environment
        self.__configuration = configuration
        self.__time_start = timer()
        self.__recorder = None

    @property
    def running_time(self) -> float:
        """
        Returns the number of seconds (wall-clock time) that have elapsed
        since this sandbox session begun.
        """
        return timer() - self.__time_start

    @property
    def state(self) -> State:
        """
        The last observed state of the system under test.
        """
        return self.__state

    @property
    def state_initial(self) -> State:
        """
        The initial state of the system under test.
        """
        return self.__state_initial

    @property
    def configuration(self) -> Configuration:
        """
        The configuration used by the system under test.
        """
        return self.__configuration

    @property
    def environment(self) -> Environment:
        """
        A description of the simulated environment.
        """
        return self.__environment

    @property
    def container(self) -> Container:
        """
        The BugZoo container underlying this sandbox.
        """
        return self.__container

    @property
    def recorder(self) -> Recorder:
        """
        The recorder object to record states during execution.
        """
        return self.__recorder

    def set_recorder(self, filename: str = '') -> Recorder:
        """
        Set the recorder.
        """
        self.__recorder = Recorder(filename=filename)
        return self.__recorder

    def unset_recorder(self) -> None:
        """
        Unset the recorder.
        """
        self.__recorder = None

    def start(self) -> None:
        """
        Starts the SITL instance for this sandbox.
        """
        raise NotImplementedError

    def stop(self) -> None:
        """
        Stops the SITL instance for this sandbox.
        """
        raise NotImplementedError

    def issue(self, command: Command) -> None:
        """
        Non-blocking for now.
        """
        # FIXME send message via connection
        command.dispatch(self,
                         self.state,
                         self.configuration,
                         self.environment)

    def run_command(self,
                    command: Command,
                    *,
                    timeout: Optional[float] = None
                    ) -> CommandOutcome:
        logger.debug('running command: %s', command)

        env = self.environment
        config = self.configuration
        time_start = self.running_time
        state_after = state_before = self.state

        # determine which spec the system should observe
        spec = command.resolve(state_before, env, config)
        postcondition = spec.postcondition

        def is_sat() -> bool:
            return postcondition.is_satisfied(command,
                                              state_before,
                                              state_after,
                                              env,
                                              config)

        logger.debug('enforcing specification: %s', spec)

        # determine timeout using specification is no timeout
        # is provided
        if timeout is None:
            timeout = command.timeout(state_before, env, config)
        logger.debug("enforcing timeout: %.3f seconds", timeout)

        self.issue(command)

        # FIXME block until completion message or timeout occurs
        time_elapsed = 0.0
        time_start = timer()
        while not is_sat() and time_elapsed < timeout:
            self.observe()
            state_after = self.state
            time.sleep(0.1)
            time_elapsed = timer() - time_start

        passed = is_sat()
        outcome = CommandOutcome(command,
                                 passed,
                                 state_before,
                                 state_after,
                                 time_elapsed)
        return outcome

    def run(self,
            commands: Sequence[Command],
            recorder_filename: Optional[str] = None
            ) -> 'MissionOutcome':
        """
        Executes a mission, represented as a sequence of commands, and
        returns a description of the outcome.
        """
        from .mission import MissionOutcome
        config = self.configuration
        env = self.environment
        time_start = timer()
        time_elapsed = 0.0
        if recorder_filename:
            self.set_recorder(recorder_filename)
        with self.__lock:
            outcomes = []  # type: List[CommandOutcome]
            passed = True
            for cmd in commands:
                if recorder_filename:
                    self.recorder.write("C: {}".format(cmd.to_dict()))
                outcome = self.run_command(cmd)
                if recorder_filename:
                    self.recorder.write_and_flush()
                outcomes.append(outcome)
                if not outcome.successful:
                    passed = False
                    break
            time_elapsed = timer() - time_start
            self.unset_recorder()
            return MissionOutcome(passed, outcomes, time_elapsed)

    def observe(self) -> None:
        """
        Triggers an observation of the current state of the system under test.
        """
        state_class = self.state.__class__
        variables = state_class.variables
        values = {name: v.read(self) for (name, v) in variables.items()}
        values['time_offset'] = self.running_time
        state_new = state_class(**values)
        with self.__state_lock:
            self.__state = state_new

    def update(self, message: Message) -> None:
        with self.__state_lock:
            self.__state = self.__state.evolve(message, self.running_time)
            if self.recorder:
                self.recorder.add(self.__state)
