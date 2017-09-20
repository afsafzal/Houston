"""
TODO: module description
"""
import branch
import state
import random

from valueRange import ValueRange


class Action(object):
    """
    Description of the concept of "Actions".
    """

    @staticmethod
    def from_json(jsn):
        """
        Constructs an Action object from its JSON description.
        """
        assert isinstance(jsn, dict)
        assert ('kind' in jsn)
        assert ('parameters' in jsn)
        return Action(jsn['kind'], jsn['parameters'])


    def __init__(self, kind, values):
        """
        Constructs an Action description.

        Args:
            kind    (str):  the name of the schema to which the action belongs
            values  (dict): a dictionary of parameter values for the action
        """
        assert (isinstance(kind, str) or isinstance(kind, unicode))
        assert isinstance(values, dict)
        self.__kind = kind
        self.__values = values.copy()


    @property
    def schema(self):
        """
        The name of the schema to which this action belongs.
        """
        return self.__kind


    def __getattr__(self, param):
        """
        Returns the value for a specific parameter in this action.
        """
        return self.__values[param]


    @property
    def values(self):
        """
        Returns a copy of the parameter values used by this action.
        """
        return self.__values.copy()


    def toJSON(self):
        """
        Returns a JSON description of this action.
        """
        return {
            'kind': self.__kind,
            'parameters': self.values
        }


class Parameter(object):
    """
    Docstring.
    """

    def __init__(self, name, value_range):
        """
        Constructs a Parameter object.

        Args:
            name (str):                 the name of this parameter.
            value_range (ValueRange):   the range of possible values for this
                parameter, given as a ValueRange object.
        """
        # TODO: type checking
        assert (isinstance(name, str) or isinstance(name, unicode))
        assert (isinstance(value_range, ValueRange))
        self.__name = name
        self.__value_range = value_range


    def values(self):
        """
        The range of possible values for this parameter.
        """
        return self.__value_range


    def generate(self, rng):
        """
        Returns a randomly-generated value for this parameter.
        """
        assert (isinstance(rng, random.Random) and rng is not None)
        return self.__value_range.sample(rng)


    @property
    def type(self):
        """
        The underlying type of this parameter.
        """
        return self.__value_range.type

    
    @property
    def name(self):
        """
        The name of this parameter.
        """
        return self.__name


class ActionSchema(object):
    """
    Action schemas are responsible for describing the kinds of actions that
    can be performed within a given system. Action schemas describe actions
    both syntactically, in terms of parameters, and semantically, in terms of
    preconditions, postconditions, and invariants.
    """

    def __init__(self, name, parameters, branches):
        """
        Constructs an ActionSchema object.

        Args:
            name (str): name of the action schema
            parameters (list of Parameter): a list of the parameters for this
                action schema
            branches (list of Branch): a list of the possible outcomes for
                actions belonging to this schema.

        """
        assert (isinstance(name, str) and not name is None)
        assert (len(name) > 0)
        assert (isinstance(parameters, list) and not parameters is None)
        assert (all(isinstance(p, Parameter) for p in parameters))
        assert (isinstance(branches, list) and not branches is None)
        assert (all(isinstance(b, branch.Branch) for b in branches))
        assert (len(branches) > 0)

        # unique branch names
        assert (len(set(b.name for b in branches)) == len(branches))

        self.__name = name
        self.__parameters =  parameters
        self.__branches = branches


    @property
    def name(self):
        """
        The name of this schema.
        """
        return self.__name

    
    @property
    def branches(self):
        """
        A list of the branches for this action schema.
        """
        return self.__branches[:]

    
    def get_branch(self, iden):
        """
        Returns a branch belonging to this action schema using its identifier.
        """
        assert (isinstance(iden, branch.BranchID) and iden is not None)
        assert (iden.get_action_name() == self.__name)
        return self.__branches[iden.get_branch_name()]


    def dispatch(self, system, action, state, environment):
        """
        Responsible for invoking an action belonging to this schema.

        Args:
            system (System): the system under test
            action (Action): the action that is to be dispatched
            state (State): the state of the system immediately prior to the
                call to this method
            environment (Environment): a description of the environment in
                which the action is being performed
        """
        raise UnimplementedError


    def compute_timeout(self, action, state, environment):
        """
        Responsible for calculating the maximum time that this action shoud take.

        :param  action          the action that is going to be performed.
        :param  state           the state in which the system is currently on.
        :param  environment     the system environment

        :returns maximum time in seconds (as a float)
        """
        branch = self.resolve_branch(action, state, environment)
        return branch.compute_timeout(action, state, environment)


    @property
    def parameters(self):
        """
        A list of the parameters used to describe actions belonging to this schema.
        """
        return self.__parameters[:]


    def resolve_branch(self, action, initial_state, environment):
        """
        Returns the branch that is appropiate for the current action, state, and
        environment based on the current action schema.
        """
        for b in self.__branches:
            if b.is_applicable(action, initial_state, environment):
                return b
        raise Exception("failed to resolve branch")


    def generate(self, rng):
        """
        Generates an action belonging to this schema at random.
        """
        assert (isinstance(rng, random.Random) and rng is not None)
        values = {p.name: p.generate(rng) for p in self.__parameters}
        return Action(self.__name, values)


class ActionOutcome(object):
    @staticmethod
    def fromJSON(jsn):
        """
        TODO: add comment
        """
        assert (isinstance(jsn, dict) and not jsn is None)
        assert ('successful' in jsn)
        assert ('action' in jsn)
        assert ('stateBefore' in jsn)
        assert ('stateAfter' in jsn)
        assert ('timeElapsed' in jsn)
        assert ('branchID' in jsn)
        assert (isinstance(jsn['branchID'], str) or isinstance(jsn['branchID'], unicode))
        assert (jsn['branchID'] is not None)
        assert (jsn['branchID'] != '')
        assert (isinstance(jsn['successful'], bool) and not jsn['successful'] is None)

        return ActionOutcome(Action.fromJSON(jsn['action']),
                             jsn['successful'],
                             state.State.fromJSON(jsn['stateBefore']),
                             state.State.fromJSON(jsn['stateAfter']),
                             jsn['timeElapsed'],
                             branch.BranchID.fromJSON(jsn['branchID']))


    """
    Used to describe the outcome of an action execution in terms of system state.
    """
    def __init__(self, action, successful, state_before, state_after, time_elapsed, branch_id):
        """
        Constructs a ActionOutcome.

        :param  action      the action that was performed
        :param  succesful   a flag indicating if the action was completed \
                            successfully
        :param  stateBefore the state of the system immediately prior to execution
        :param  stateAfter  the state of the system immediately after execution
        :param  branchID    the identifier of the branch that was taken \
                            during the execution of this action
        """
        assert isinstance(action, Action)
        assert isinstance(successful, bool)
        assert isinstance(state_before, state.State)
        assert isinstance(state_after, state.State)
        assert isinstance(time_elapsed, float)
        assert isinstance(branch_id, branch.BranchID)

        self.__action      = action
        self.__successful  = successful
        self.__state_before = state_before
        self.__state_after  = state_after
        self.__time_elapsed = time_elapsed
        self.__branch_id = branch_id


    def toJSON(self):
        """
        Returns a JSON description of this action outcome.
        """
        return {
            'action':       self.__action.toJSON(),
            'successful':   self.__successful,
            'stateBefore':  self.__state_before.toJSON(),
            'stateAfter':   self.__state_after.toJSON(),
            'timeElapsed':  self.__time_elapsed,
            'branchID':     self.__branch_id.toJSON()
        }

    
    def getBranchID(self):
        """
        Returns an identifier for the branch that was taken by this action.
        """
        return self.__branch_id


    @property
    def passed(self):
        """
        Returns true if this action was successful.
        """
        return self.__successful

    
    @property
    def failed(self):
        """
        Returns true if this action was unsuccessful.
        """
        return not self.__successful


    @property
    def state_after(self):
        """
        A description of the state of the system immediately after the
        execution of this action.
        """
        return self.__state_after


    @property
    def state_before(self):
        """
        A description of the state of the system immediately before the
        execution of this action.
        """
        return self.__start_before


class ActionGenerator(object):

    def __init__(self, schema_name, parameters = []):
        """
        Constructs a new action generator.

        :param  schemaName: the name of the schema for which this generator \
                    produces actions.
        :params parameters: a list of the parameters to this generator.
        """
        assert (isinstance(schema_name, str) and schema_name is not None)
        assert (isinstance(parameters, list) and parameters is not None)

        self.__schema_name = schema_name
        self.__parameters = parameters


    def construct_with_state(self, current_state, env, values):
        """
        Responsible for constructing a dictionary of Action arguments based
        on the current state of the robot, a description of the environment,
        and a dictionary of generator parameter values.

        :returns    a dictionary of arguments for the generated action
        """
        raise NotImplementedError


    def construct_without_state(self, env, values):
        """
        Responsible for constructing a dictionary of Action arguments based
        on the current state of the robot, a description of the environment,
        and a dictionary of generator parameter values.

        :returns    a dictionary of arguments for the generated action
        """
        raise NotImplementedError


    @property
    def schema_name(self):
        """
        The name of the schema to which actions generated by this
        generator belong.
        """
        return self.__schema_name


    def generate_action_with_state(self, current_state, env, rng):
        assert (isinstance(rng, random.Random) and rng is not None)
        values = {p.name: p.generate(rng) for p in self.__parameters}
        values = self.construct_with_state(current_state, env, values)
        return Action(self.__schema_name, values)


    def generate_action_without_state(self, env, rng):
        assert (isinstance(rng, random.Random) and rng is not None)
        values = {p.name: p.generate(rng) for p in self.__parameters}
        values = self.construct_without_state(env, values)
        return Action(self.__schema_name, values)
