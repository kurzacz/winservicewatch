import rpyc
from rpyc.utils.helpers import classpartial
from rpyc.utils.server import ThreadedServer

import threading
import logging

import sys
import os
import time

import signal


class AppClient:

    class PortThread(threading.Thread):

        class Port(rpyc.Service):
            def __init__(self, app):
                super().__init__()
                self._app = app

            def on_connect(self, conn):
                # code that runs when a connection is created
                # (to init the service, if needed)
                pass

            def on_disconnect(self, conn):
                # code that runs after the connection has already closed
                # (to finalize the service, if needed)
                pass

            def exposed_updateServiceState(self, state):
                self._app.setServiceState(state)
                logging.getLogger().debug('Status updated! Changed to: '+ str(state))

        def __init__(self, app):
            threading.Thread.__init__(self)
            self._app = app

        def run(self):
            logging.getLogger().debug('PortThread: Starting thread...')
            self.startPort()
            logging.getLogger().debug('PortThread: Thread finished')

        def startPort(self):
            portConstructor = classpartial(self.Port, self._app)
            self._portServer = ThreadedServer(portConstructor, port=18870)
            self._portServer.start()

        def closePort(self):
            self._portServer.close()

    def __init__(self):
        self._serviceState = None

        self._portThread = self.PortThread(self)
        self._portThread.start()

        logging.getLogger().info('Started client with port thread')

    def subscribeToService(self):
        # polaczenie z usluga
        self._servicePort = rpyc.connect("localhost", 18860)
        self._servicePort.root.register_observer(18870, 'testClient')
        self._serviceState = self._servicePort.root.get_state()
        logging.getLogger().info("Present state: {}".format(self._serviceState))
        # zamykam wychodzace polaczenie z usluga
        #self._servicePort.close()

    def unsubscribeFromService(self):
        # polaczenie z usluga
        #self._servicePort = rpyc.connect("localhost", 18860)
        self._servicePort.root.remove_observer('testClient')
        # zamykam wychodzace polaczenie z usluga
        self._servicePort.close()

    def setServiceState(self, state):
        self._serviceState = state

    def closeApp(self):
        logging.getLogger().info('Zamykam polaczenie')
        self.unsubscribeFromService()
        # zamknij polaczenia przychodzace
        self._portThread.closePort()


logs = logging.getLogger()
logs.setLevel(logging.DEBUG)
handlerConsole = logging.StreamHandler()
handlerConsole.setLevel(logging.DEBUG)
formatterMain = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    '%Y-%m-%d %H:%M:%S'
)
handlerConsole.setFormatter(formatterMain)
logs.addHandler(handlerConsole)



app = AppClient()
app.subscribeToService()


while True:
    nb = input('Type `q` to close: ')
    if nb == 'q':
        break

app.closeApp()
