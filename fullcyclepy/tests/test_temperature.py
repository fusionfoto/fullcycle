'''test telegram api'''

from backend.fcmapp import ApplicationService, ComponentName

APP = ApplicationService(ComponentName.fullcycle)

HUMID, TEMPER = APP.readtemperature()

MESSAGE = '{0}: Temp={1:0.1f}*  Humidity={2:0.1f}%'.format(APP.now(), TEMPER, HUMID)

APP.sendtelegrammessage(MESSAGE)

APP.shutdown()
