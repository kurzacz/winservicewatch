import logging
import schedule
import time
import winservicewatch.Service


class MyServiceGate(winservicewatch.Service.ServiceGate):

    def exposed_get_state(self):
        """
        This is custom function to retrieve some variable from MyObservableService

        Provide this function to let observer get service state immediately after connection establish.
        Please note the exposed_ prefix, required by RPYC: https://rpyc.readthedocs.io/en/latest/docs/services.html

        :returns: value of a field you want to expose
        :rtype: int
        """

        return self._observedService.get_state()


class MyObservableService(winservicewatch.Service.WinService):

    STATE_BUSY = 1
    """Class const of state when your service performs any demanding task"""

    STATE_IDLE = 0
    """Class const of state when your service is waiting until schedule call main job again"""

    def __init__(self, args):
        super().__init__(args)
        self._state = MyObservableService.STATE_IDLE
        self._serviceGateThread = winservicewatch.Service.ServiceGateThread(self, MyServiceGate, 18860)

    def main(self):
        logging.getLogger().info("Starting main loop")

        timer = schedule.every(15).seconds
        timer.do(self.my_job)
        while self._is_running:
            schedule.run_pending()
            time.sleep(1)

    def my_job(self):
        logging.getLogger().info("Starting main job")

        logging.getLogger().debug("Suppose I'm locking resources. Set busy state")
        self._state = MyObservableService.STATE_BUSY
        self._notify_observers()
        logging.getLogger().info("Starting job...")
        time.sleep(5)
        logging.getLogger().debug("Finished. Unlock resources then switch back to idle state")
        self._state = MyObservableService.STATE_IDLE
        self._notify_observers()

    def _notify_observers(self):
        logging.getLogger().info("Notify observers about state change")
        for name in self._observers:
            self._observers[name].root.updateServiceState(self._state)

    def get_state(self):
        return self._state


loggerMain = logging.getLogger()
loggerMain.setLevel(logging.DEBUG)
handlerConsole = logging.StreamHandler()
handlerConsole.setLevel(logging.DEBUG)
formatterMain = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    '%Y-%m-%d %H:%M:%S'
)
handlerConsole.setFormatter(formatterMain)
loggerMain.addHandler(handlerConsole)

if __name__ == '__main__':
    MyObservableService.parse_command_line()
