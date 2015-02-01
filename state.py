'''
''
'' Python RescueJumper-like state machine
''
'''



class BaseState(object):

    def start(self, data):
        assert 0, "not implemented"

    def update(self, data):
        assert 0, "not implemented"

    def end(self, data=None):
        assert 0, "not implemented"

    def should_trigger(self, data):
        assert 0, "not implemented"

    @property
    def priority(self):
        if hasattr(self, '_priority'):
            return self._priority
        return 0

    @property
    def keep_me(self):
        if hasattr(self, '_keep_me'):
            return self._keep_me
        return True

    @property
    def next_state(self):
        if hasattr(self, '_next_state'):
            return self._next_state
        return None






class StateMachine(object):

    def __init__(self):
        self._states = []
        self._current_state = None

    def update(self, data):
        # call update(data) on current active state
        if self._current_state is not None:
            response = self._current_state.update(data)
            if response == False: # state responded False, means he has finished by himself
                self._current_state.end(data)
                self.stop_state_log(self._current_state)

                # if state wants to be removed from the list
                state = self._current_state
                self._current_state = None
                if state.keep_me == False:
                    self.remove_state(state)

                # if state has a forced following state
                next_state = state.next_state
                if next_state is not None:
                    self._current_state = next_state
                    self.start_state_log(self._current_state)
                    self._current_state.start(data)
                    return True
        
        # check if any state wants the lead
        selected_state = self._current_state
        for state in self._states:
            if state == self._current_state:
                continue
            if (selected_state is None or selected_state.priority < state.priority) \
                and state.should_trigger(data) == True:
                selected_state = state

        # a state is elligible to leadership
        if selected_state != self._current_state:
            if self._current_state is not None:
                self.stop_state_log(self._current_state)
                self._current_state.end(data)

                # TODO DRY
                state = self._current_state
                self._current_state = None
                if state.keep_me == False:
                    self.remove_state(state)

            self._current_state = selected_state
            self.start_state_log(self._current_state)
            self._current_state.start(data)

        return self._current_state is not None # say that there is a state currently active

    def start_state_log(self, state):
        pass
        #print('Starting state: {0}({1})'.format(state.__class__.__name__, state.priority))
        
    def stop_state_log(self, state):
        pass
        #print('Stopping state: {0}({1})'.format(self._current_state.__class__.__name__, self._current_state.priority))

    def add_state(self, state):
        state.machine = self
        self._states.append(state)

    def remove_state(self, state):
        if state == self._current_state:
            self.stop_state_log(state)
            self._current_state.end()
        self._states.remove(state)

    def kill_self(self):
        self._states = []
