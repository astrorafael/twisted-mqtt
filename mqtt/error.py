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

class QoSValueError(ValueError):
    '''QoS value not within [0..3] range'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '{0}: {1} {2}'.format(s, self.args[0], self.args[1])
        s = '{0}.'.format(s)
        return s

class KeepaliveValueError(ValueError):
    '''Keepalive value out of range'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '{0}: {1}'.format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

class ClientIdValueError(ValueError):
    '''Client id string length out of range'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '{0}: {1}'.format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

class ProtocolValueError(ValueError):
    '''Incorrect protocol version'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '{0}: {1!s}'.format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

class MissingTopicError(ValueError):
    '''Missing topic'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '{0}: in {1}'.format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

class MissingPayloadError(ValueError):
    '''Missing payload'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = '{0}: in {1}'.format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

class MissingUserError(ValueError):
    '''Missing username in connect'''
    def __str__(self):
        s = self.__doc__
        return s


class TimeoutValueError(ValueError):
    '''Protocol timeout value out of range'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = "{0}: {1}".format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

class WindowValueError(ValueError):
    '''Max. number of allowed in-flight messages out of range'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = "{0}: {1}".format(s, self.args[0])
        s = '{0}.'.format(s)
        return s


class ProfileValueError(ValueError):
    '''MQTT client profile value not supported'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = "{0}: {1}".format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

class PayloadValueError(ValueError):
    '''Payload too large'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = "{0}: {1}".format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

class StringValueError(ValueError):
    '''MQTT strings exceeds 65535 bytes'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = "{0}: {1}".format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

class TopicTypeError(TypeError):
    '''Subscribe topic type is not a list'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = "{0}: {1!s}".format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

class PayloadTypeError(TypeError):
    '''Type not allowed as payload'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = "{0}: {1!s}".format(s, self.args[0])
        s = '{0}.'.format(s)
        return s

class MQTTError(Exception):
    '''Base class for all exceptions below'''
    pass


class MQTTStateError(MQTTError):
    '''MQTT protocol state error'''
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
