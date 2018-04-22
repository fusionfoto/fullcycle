'''
# listens for statistics updated and run rules on them
# some rules can run just from the last statistics
# other rules will need to be enforced from the history of the miner
'''
import datetime
import json
from colorama import Fore
from helpers.queuehelper import QueueName, QueueEntries
from domain.mining import MinerCommand
from domain.miningrules import MinerStatisticsRule
from domain.logging import MinerLog
from fcmapp import ComponentName, Component

class ComponentRunRules(Component):
    '''component for running rules'''
    def __init__(self):
        self.alertstext = ''
        super().__init__(componentname=ComponentName.rules, option='')

    def addalert(self, alertmsg):
        self.alertstext += alertmsg
        return alertmsg

RULES = ComponentRunRules()

def rules(miner, minerstats, minerpool):
    '''this runs the rules'''
    entries = QueueEntries()
    if miner is None or minerstats is None:
        return entries
    savedminer = RULES.app.getminer(miner)
    cmd_restart = MinerCommand('restart', '')
    broken = []
    for ruleparms in RULES.app.ruleparameters():
        rule = MinerStatisticsRule(savedminer, minerstats, ruleparms)
        if rule.isbroken():
            broken += rule.brokenrules

    if broken:
        RULES.app.alert('\n'.join([b.parameter for b in broken]))
        #TODO: could raise broken rule event???
        for rule in broken:
            log = MinerLog()
            log.createdate = datetime.datetime.utcnow()
            log.minerid = rule.miner.key()
            log.minername = rule.miner.name
            log.action = rule.parameter
            RULES.app.log_mineractivity(log)

            if rule.action == 'alert':
                entries.addalert(RULES.addalert(rule.parameter))
            elif rule.action == 'restart':
                entries.add(QueueName.Q_RESTART, RULES.app.createmessagecommand(rule.miner, cmd_restart))
                entries.addalert(RULES.addalert('Restarted {0}'.format(rule.miner.name)))
            else:
                RULES.app.logerror('did not process broken rule {0}'.format(rule.parameter))

    return entries

def when_statisticsupdated(channel, method, properties, body):
    '''when miner stats are pulled from miner...'''
    print("[{0}] Received miner stats".format(RULES.app.now()))
    try:
        msg = RULES.app.messagedecodeminerstats(body)
        entries = dorules(msg.miner, msg.minerstats, msg.minerpool)
        RULES.app.enqueue(entries)
    except json.decoder.JSONDecodeError as jex:
        RULES.app.logexception(jex)
        RULES.app.logdebug(RULES.app.exceptionmessage(jex))
        RULES.app.logdebug(RULES.app.safestring(body))
    except BaseException as ex:
        RULES.app.logexception(ex)
        RULES.app.logdebug(RULES.app.exceptionmessage(ex))
        RULES.app.logdebug(RULES.app.safestring(body))

def dorules(miner, minerstats, minerpool):
    '''run the rules on them'''
    RULES.alertstext = ''
    entries = rules(miner, minerstats, minerpool)
    if RULES.alertstext:
        print(Fore.RED + RULES.alertstext)
    print("Rules executed for {0}".format(miner.name))
    return entries

def main():
    if RULES.app.isrunnow:
        for (miner, stats, pool) in RULES.app.getminerstatscached():
            rules(miner, stats, pool)
        RULES.app.shutdown()
    else:
        queue_stats = RULES.app.makebroadcastlistener(QueueName.Q_STATISTICSUPDATED)

        print('Waiting for statisticsupdated on {0}. To exit press CTRL+C'.format(queue_stats.queue_name))

        queue_stats.subscribe(when_statisticsupdated)

        RULES.app.listen(queue_stats)

if __name__ == "__main__":
    main()
