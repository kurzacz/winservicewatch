import socket
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
    """Base class to create winservice in Python"""

    _svc_name_ = 'pythonService'
    _svc_display_name_ = 'Python Service'
    _svc_description_ = 'Python Service Description'

    @classmethod
    def parse_command_line(cls):
        """
        ClassMethod to parse the command line
        """
        win32serviceutil.HandleCommandLine(cls)

    def __init__(self, args):
        """
        Constructor of the winservice
        """
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        """
        Called when the service is asked to stop
        """
        self.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        """
        Called when the service is asked to start
        """
        self.start()
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def start(self):
        """
        Override to add logic before the start
        eg. running condition
        """
        pass

    def stop(self):
        """
        Override to add logic before the stop
        eg. invalidating running condition
        """
        pass

    def main(self):
        """
        Main class to be ovverridden to add logic
        """
        pass


class ServiceGate(rpyc.Service):
    """
    Allows to establish incoming connection to the WinService
    """

    def __init__(self, observed):
        """
        Init the gate which gives access for the WinService

        :param observed: Reference to observed WinService
        :type observed: ref
        """

        super().__init__()
        self._observedService = observed

    def on_connect(self, conn):
        pass

    def on_disconnect(self, conn):
        pass

    def exposed_register_observer(self, port, name):
        """
        Register object that will be notified on WinService state change

        This example assumes that observer is on the same host (localhost) as observable

        :param port: The Windows port on which the observer was registered.
            You can use for example rpyc ThreadedServer:
            https://rpyc.readthedocs.io/en/latest/api/utils_server.html#rpyc.utils.server.ThreadedServer
        :type port: int
        :param name: Friendly name which you can use to distinguish observers
        :type name: str
        """

        handler = rpyc.connect("localhost", port)
        self._observedService.register_observer(name, handler)

    def exposed_remove_observer(self, name):
        """
        Unregister observer previously added to notification list

        :param name: Friendly name you used to register observer
        :type name: str
        """
        self._observedService.remove_observer(name)


class ServiceGateThread (threading.Thread):
    """
    This class starts and handle dedicated thread for ServiceGate. It's a clutch between WinService and ServiceGate.
    """

    def __init__(self, observed, service_gate, port):
        """
        Init the thread object.

        Because this object is a bridge between WinService and ServiceGate, reference to original
            observed service is required. This reference will be passed to ServiceGate then. Please
            provide child class of ServiceGate as well as port on which you gate will be available.

        :param observed: Reference to observed WinService
        :type observed: ref
        :param service_gate: Class inherited from ServiceGate
        :type service_gate: class name
        :param port: Port number on which you wish to access your service
        :type port: int
        """

        threading.Thread.__init__(self)
        self._observedService = observed
        self._gateClass = service_gate
        self._port = port

    def run(self):
        """
        Starts and keep running ServiceGate on dedicated thread

        Rpyc package offers builders for services, which is blocking.
            For that reason, it must run on another thread, otherwise it will block your app. See more:
            https://rpyc.readthedocs.io/en/latest/api/utils_server.html#rpyc.utils.server.Server.start
        """
        logging.getLogger().debug('Starting thread for ServiceGate')
        service = classpartial(self._gateClass, self._observedService)
        t = ThreadedServer(service, port=self._port)
        t.start()
        logging.getLogger().debug('Thread for ServiceGate finished running')


class WinService(SMWinservice):
    """
    WinService class you wish to observe

    This class contains service name as well as description you will see on Windows when run Services.msc
    """

    _svc_name_ = "TestPythonWinService"
    """Name you use in e.g. cmd to run/stop/check status."""

    _svc_display_name_ = "TestPythonWinService"
    """Friendly name you will see in services."""

    _svc_description_ = "Example long service with exposed changing state"
    """Short description of your service name."""

    def __init__(self, args):
        """
        Init object and set service gate.

        You need to override _serviceGateThread with ServiceGateThread object created with your custom arguments.

        :param args: args set when service is started by Windows.
        """

        super().__init__(args)
        self._observers = {}  # dict()
        self._is_running = False
        self._serviceGateThread = None

    def start(self):
        """
        Interface function for starting the service

        This method will be called when you try to start the service from Windows service panel or cmd.
        """
        logging.getLogger().info("Starting main observed service")
        self._is_running = True

        self._serviceGateThread.start()

    def stop(self):
        """
        Interface function for stopping the service

        This method will be called when you ask your service to stop.
        """
        logging.getLogger().info("Main observed service is about to stop")
        self._is_running = False

    def _notify_observers(self):
        pass

    def register_observer(self, name, handler):
        self._observers[name] = handler
        logging.getLogger().debug("Added obsever %s" % name)

    def remove_observer(self, name):
        del (self._observers[name])
        logging.getLogger().debug("Deleted observer %s" % name)

    def main(self):
        """
        Interface function of main service task.

        This method will be called when you ask your service to start.
        """

        pass
