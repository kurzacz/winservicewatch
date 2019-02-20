import socket
import random
import sys
import rpyc
from rpyc.utils.server import ThreadedServer
from rpyc.utils.helpers import classpartial


import win32serviceutil

import servicemanager
import win32event
import win32service

import schedule
import time

import logging.handlers
import threading

class SMWinservice(win32serviceutil.ServiceFramework):
    '''Base class to create winservice in Python'''

    _svc_name_ = 'pythonService'
    _svc_display_name_ = 'Python Service'
    _svc_description_ = 'Python Service Description'

    @classmethod
    def parse_command_line(cls):
        '''
        ClassMethod to parse the command line
        '''
        win32serviceutil.HandleCommandLine(cls)

    def __init__(self, args):
        '''
        Constructor of the winservice
        '''
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        '''
        Called when the service is asked to stop
        '''
        self.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        '''
        Called when the service is asked to start
        '''
        self.start()
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def start(self):
        '''
        Override to add logic before the start
        eg. running condition
        '''
        pass

    def stop(self):
        '''
        Override to add logic before the stop
        eg. invalidating running condition
        '''
        pass

    def main(self):
        '''
        Main class to be ovverridden to add logic
        '''
        pass

class MyService(rpyc.Service):
    def __init__(self, observed):
        super().__init__()
        self._observedService = observed

    def on_connect(self, conn):
        pass

    def on_disconnect(self, conn):
        pass

    def exposed_get_state(self): # this is an exposed method
        return self._observedService._state

    def exposed_registerObserver(self, port, name):
        self._observedService._observers[name] = rpyc.connect("localhost", port)
        logging.getLogger().debug(
            "Added obsever {}".format(name))

    def exposed_removeObserver(self, name):
        del(self._observedService._observers[name])
        logging.getLogger().debug("Deleted observer {}".format(name))

class InfoPortThread (threading.Thread):
    def __init__(self, testService):
        threading.Thread.__init__(self)
        self.testService = testService

    def run(self):
        logging.getLogger().debug('Starting Info Port')
        service = classpartial(MyService, self.testService)
        t = ThreadedServer(service, port=18860)
        t.start()
        logging.getLogger().debug('Stopped info port thread')

class TestService(SMWinservice):
    _svc_name_ = "TestService"
    _svc_display_name_ = "Test service"
    _svc_description_ = "xxx"

    STATE_BUSY = 1
    STATE_IDLE = 0

    def __init__(self, args):
        super().__init__(args)
        self.loggerMain = logging.getLogger()
        self.loggerMain.setLevel(logging.DEBUG)
        self.handlerConsole = logging.StreamHandler()
        self.handlerConsole.setLevel(logging.DEBUG)
        self.formatterMain = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
        self.handlerConsole.setFormatter(self.formatterMain)
        self.loggerMain.addHandler(self.handlerConsole)

        self._observers = {}  # dict()
        self._state=TestService.STATE_IDLE

    def start(self):
        self.loggerMain.info("Starting main service")
        self.isrunning = True

        self.infoPortThread = InfoPortThread(self)
        self.infoPortThread.start()

    def stop(self):
        self.loggerMain.info("Stopping main service")
        self.isrunning = False

    def refreshRoutersBalance(self):
        self.loggerMain.info("Starting main job")

        self.loggerMain.debug("Setting busy state")
        self._state = TestService.STATE_BUSY
        self.notifyObservers()
        self.loggerMain.info("Starting session...")
        time.sleep(15)
        self.loggerMain.debug("Finished. Switching back to idle state")
        self._state = TestService.STATE_IDLE
        self.notifyObservers()

    def notifyObservers(self):
        self.loggerMain.info("Notify observers about state change")
        for name in self._observers:
            self._observers[name].root.updateServiceState(self._state)


    def main(self):
        self.loggerMain.info("Starting main loop")

        timer = schedule.every(12).seconds
        timer.do(self.refreshRoutersBalance)
        while self.isrunning:
            schedule.run_pending()
            time.sleep(1)

if __name__ == '__main__':
    TestService.parse_command_line()