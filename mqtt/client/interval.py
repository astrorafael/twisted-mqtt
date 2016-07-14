import random

class Interval(object):
    '''
    This class build automatically incrementing interval objects, 
    to be used in requests timeouts
    
    Use like:
    C{interval = Interval()}
    C{t = interval()}
    C{t = interval()}

    @ivar initial:  Initial interval value, in seconds.
    @ivar maxDelay: maximun interval value produced, in seconds.
    @ivar factor:   multiplier for the next interval.
    '''
   
    
    def __init__(self, initial=2, maxDelay=1024, factor=2):
        '''Initialize interval object'''
        self.initial  = initial
        self.factor   = factor
        self.maxDelay = max(initial, maxDelay)
        self._value   = self.initial


    def __call__(self):
        '''Call the interval to produce a new delay time'''
        self._value *= self.factor
        self._value = min(self._value, self.maxDelay)
        return self._value + random.random()

class IntervalLinear(object):
    '''
    This class build automatically incrementing interval objects, 
    to be used in requests timeouts. This variant takes estimates 
    of bandwidth and Payload size and and exponential backoff
    lowering the bandwith = bandwith/factor with each new call.
    
    Use like:
    C{interval = IntervalLinear()}
    C{t = interval()}
    C{t = interval()}

    @ivar initial:  Initial interval value, in seconds.
    @ivar factor:   multiplier for the next interval.
    @ivar bandwith: estimated bandwith in bytes/sec.
    '''
    
    def __init__(self, initial=2,  factor=2, bandwith=1):
        '''Initialize interval object'''
        self.initial  = initial
        self.factor   = factor
        self.bandwith = bandwith
        self._k       = 1
        self._value   = self.initial


    def __call__(self, size):
        '''Call the interval to produce a new delay time taking into account the bandwith'''
        self._value = self.initial + (self._k*size)/self.bandwith
        self._k    *= self.factor
        return self._value + random.random()