'''#runs tasks on schedule
#should read tasks from configuration
#examples: when to discover. when to monitor. when to ...
#will run tasks by sending command (raising event)
'''
import datetime
import time
from helpers.queuehelper import QueueName, QueueEntry
from helpers.taskschedule import TaskSchedule
from fcmapp import ApplicationService

#one-time schedule provision when app starts up
APP = ApplicationService(component='schedule')
APP.send(QueueName.Q_POOLCONFIGURATIONCHANGED, '')
SLEEP_SECONDS = APP.configuration('schedule.sleep.seconds')

HEARTBEAT = TaskSchedule(run_on_init=True)
HEARTBEAT.start = datetime.datetime.now().replace(microsecond=0, second=0, minute=0) + datetime.timedelta(hours=1)
HEARTBEAT.interval = 60 * APP.configuration('schedule.hearbeat.minutes')

MONITOR = TaskSchedule()
MONITOR.interval = APP.configuration('schedule.monitor.seconds')

DISCOVER = TaskSchedule()
DISCOVER.interval = 60 * APP.configuration('schedule.discover.minutes')

CAMERA = TaskSchedule(run_on_init=False)
CAMERA.start = datetime.datetime.now().replace(microsecond=0, second=0, minute=0) + datetime.timedelta(hours=1)
CAMERA.interval = 60 * APP.configuration('schedule.camera.minutes')

TEMPERATURE = TaskSchedule(run_on_init=False)
TEMPERATURE.start = datetime.datetime.now().replace(microsecond=0, second=0, minute=0) + datetime.timedelta(hours=1)
TEMPERATURE.interval = 60 * APP.configuration('schedule.temperature.minutes')

while True:
    try:
        if MONITOR.is_time_to_run():
            print("[{0}] Time to monitor".format(APP.now()))
            print('Pushing monitor command to {0}.'.format(QueueName.Q_MONITOR))
            APP.send(QueueName.Q_MONITOR, 'monitor')
            MONITOR.lastrun = datetime.datetime.now()

        if DISCOVER.is_time_to_run():
            print("[{0}] Time to discover".format(APP.now()))
            print('Pushing discover command to {0}.'.format(QueueName.Q_DISCOVER))
            APP.send(QueueName.Q_DISCOVER, 'discover')
            DISCOVER.lastrun = datetime.datetime.now()

        if CAMERA.is_time_to_run():
            print("[{0}] sending camera".format(APP.now()))
            APP.take_picture('fullcycle_camera.png')
            APP.sendtelegramfile('fullcycle_camera.png')
            CAMERA.lastrun = datetime.datetime.now()

        if TEMPERATURE.is_time_to_run():
            print("[{0}] sending temperature".format(APP.now()))
            SENSOR_HUMID, SENSOR_TEMP = APP.readtemperature()
            if SENSOR_HUMID is not None or TEMPERATURE is not None:
                MESSAGE = '{0}: Temp={1:0.1f}*  Humidity={2:0.1f}%'.format(APP.now(), SENSOR_TEMP, SENSOR_HUMID)
                APP.sendtelegrammessage(MESSAGE)
            TEMPERATURE.lastrun = datetime.datetime.now()

        if HEARTBEAT.is_time_to_run():
            print("[{0}] sending heartbeat".format(APP.now()))
            #get summary of known miners. name, hash or offline, pool
            SENSOR_HUMID, SENSOR_TEMP = APP.readtemperature()
            if SENSOR_HUMID is not None and SENSOR_TEMP is not None:
                MSG = 'At {0} Temp={1:0.1f}*  Humidity={2:0.1f}%\n{3}'.format(APP.now(), SENSOR_TEMP, SENSOR_HUMID, APP.minersummary())
                APP.sendtelegrammessage(MSG)
                APP.sendqueueitem(QueueEntry(QueueName.Q_LOG, MSG, 'broadcast'))
            HEARTBEAT.lastrun = datetime.datetime.now()

        time.sleep(SLEEP_SECONDS)

    except KeyboardInterrupt:
        APP.shutdown()
    except BaseException as ex:
        print('App Error: ' + APP.exceptionmessage(ex))
