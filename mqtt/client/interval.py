import random

class Interval(object):
    '''
    This class build automatically incrementing interval objects, 
    to be used in requests timeouts
    
    Use like:
    C{interval = Interval()}
    C{Interval.maxDelay = 16}
    C{t = interval()}
    C{t = interval()}

    @cvar initial:  Initial interval value, in seconds.
    @cvar maxDelay: maximun interval value produced, in seconds.
    @cvar factor:   multiplier for the next interval.
    '''
    initial  = 2
    factor   = 2
    maxDelay = 1024
    
    def __init__(self, initial=2, maxDelay=1024, factor=2):
        '''Initialize interval object'''
        self.initial  = initial
        self.factor   = factor
        self.maxDelay = max(initial, maxDelay)
        self._value   = self.initial


    def __call__(self):
        '''Call the interval with an id and produce a new value for that id'''
        self._value *= self.factor
        self._value = min(self._value, self.maxDelay)
        return self._value + random.random()