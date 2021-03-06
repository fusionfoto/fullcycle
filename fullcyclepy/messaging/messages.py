'''# Full Cycle Mining Messages'''
import json
from marshmallow import Schema, fields, post_load
from messaging.schema import MinerCommandSchema, MinerSchema, MinerStatsSchema, MinerCurrentPoolSchema
from domain.mining import Miner, MinerCommand

class MessageSchema(Schema):
    '''schema for message'''
    timestamp = fields.DateTime()
    sender = fields.Str()
    type = fields.Str()
    body = fields.Str()
    version = fields.Str()

    #def make_user(self, data):
    #    return User(**data)

    @post_load
    def make_message(self, data):
        '''reconstitute a message'''
        msg = Message(data['timestamp'], data['sender'], data['type'], data['body'])
        return msg

class MinerCommandMessage(object):
    """Command that could be sent to a miner"""
    def __init__(self, command='', parameter=''):
        self.command = command
        self.parameter = parameter

#class Event(object):
#    """Event? """
#    todo = ''

class MinerMessage(object):
    """ Miner information for a message
    Miner could be None, meaning message is for all
    command could be None, meaning message is informational for a specific miner
    """
    def __init__(self, miner, command=None, minerstats=None, minerpool=None):
        self.command = command
        self.miner = miner
        self.minerstats = minerstats
        self.minerpool = minerpool

class MinerMessageSchema(Schema):
    '''schema for minermessage'''
    command = fields.Nested(MinerCommandSchema)
    miner = fields.Nested(MinerSchema)
    minerstats = fields.Nested(MinerStatsSchema)
    minerpool = fields.Nested(MinerCurrentPoolSchema)

    @post_load
    def make_minermessage(self, data):
        '''reconstitute a minermessage'''
        miner = None
        command = None
        minerstats = None
        minerpool = None
        if 'miner' in data:
            #todo:find out why miner sometimes comes in as dict instead of entity
            if isinstance(data['miner'], Miner):
                miner = data['miner']
            else:
                miner = Miner(**data['miner'])
        if 'command' in data:
            if isinstance(data['command'], MinerCommand):
                command = data['command']
            else:
                command = MinerCommand(**data['command'])
        if 'minerstats' in data:
            #minerstats = MinerStatistics(Miner=miner,**data['minerstats'])
            minerstats = data['minerstats']
        if 'minerpool' in data:
            #minerpool = MinerCurrentPool(Miner=miner, **data['minerpool'])
            minerpool = data['minerpool']
        entity = MinerMessage(miner, command, minerstats, minerpool)
        return entity


class Message(object):
    """A Full Cycle Mining Message
    Keep generic so that body can be almost anything
    A generic message envelope
    See http://marshmallow.readthedocs.io/en/latest/extending.html
    """
    def __init__(self, timestamp, sender='', message_type='', body='', version=1.1):
        self.version = version
        self.timestamp = timestamp
        self.sender = sender
        self.type = message_type
        self.body = body

    def jsonserialize(self, sch, msg):
        '''json serialize a message'''
        return json.dumps(sch.dump(msg))

    def bodyjson(self):
        '''for some reason it gets encoded as list. just return first element'''
        #todo: test why python serialization makes it a list but node does not
        jsonlist = json.loads(self.body)
        if 'miner' in jsonlist:
            return jsonlist
        return jsonlist[0]

    def bodyonlyjson(self):
        '''deserialize body of message'''
        jsononly = json.loads(self.body)
        return jsononly

    def make_any(self, message_type, body):
        '''make a message'''
        self.type = message_type
        self.body = body
        return self

    def make_minerstats(self, miner, minerstats=None, minerpool=None):
        '''make a miner stats message'''
        self.type = 'minerstats'
        minermsg = MinerMessage(miner, command=None, minerstats=minerstats, minerpool=minerpool)
        self.body = self.jsonserialize(MinerMessageSchema(), minermsg)
        return self

    def make_command(self, command):
        '''make a command message'''
        self.type = 'command'
        msg = MinerCommandMessage(command.command, command.parameter)
        self.body = self.jsonserialize(MinerCommandSchema(), msg)
        return self

    def make_minercommand(self, miner, command):
        '''make a miner commad message'''
        self.type = 'minercommand'
        minermsg = MinerMessage(miner, command=command)
        self.body = self.jsonserialize(MinerMessageSchema(), minermsg)
        return self

    #these will handled independently
    #def make_sensorvalue(self, sensorvalue):
    #    self.type = 'sensorvalue'
    #    msg = SensorValueMessage(sensor.sensorid, sensor.value)
    #    self.body = self.jsonserialize(SensorValueSchema(),msg)
    #    return self

    #def make_sensor(self, sensor):
    #    self.type = 'sensor'
    #    msg = SensorMessage(sensor.sensorid, sensor.value)
    #    self.body = self.jsonserialize(SensorSchema(),msg)
    #    return self
