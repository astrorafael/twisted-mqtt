# ----------------------------------------------------------------------
# Copyright (C) 2015 by Rafael Gonzalez 
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ----------------------------------------------------------------------

class QoSError(ValueError):
    '''QoS value not within [0..3] range'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '{0}: {1!s} {2}'.format(s, self.args[0], 
                                         ' '.join(self.args[1:]))
        s = '{0}.'.format(s)
        return s

class PayloadEncodingError(ValueError):
    '''Unknown payload encoding'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = "{0}: '{1}' for {2!s}".format(s, self.args[0], self.args[1])
        s = '{0}.'.format(s)
        return s


class MQTTError(Exception):
    '''Base class for all exceptions below'''
    pass


class MQTTStateError(MQTTError):
    '''MQTT protocol error'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = "{0}: '{1}' for {2!s}".format(s, self.args[0], self.args[1])
        s = '{0}.'.format(s)
        return s

class MQTTWindowError(MQTTError):
    '''Request exceeded maximun window size'''
    def __str__(self):
        return self.__doc__


class MQTTTimeoutError(MQTTError):
    '''Server no responding in time to expected packet'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = "{0}: '{1}'".format(s, self.args[0])
        s = '{0}.'.format(s)
        return s
