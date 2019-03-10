import logging
# TODO: Create requirements and put schedule
import schedule
import time
import winservicewatch.Service


class MyObservableService(winservicewatch.Service.WinService):

    STATE_BUSY = 1
    """Class const of state when your service performs any demanding task"""

    STATE_IDLE = 0
    """Class const of state when your service is waiting until schedule call main job again"""

    def __init__(self, args):
        super().__init__(args)
        self._state = MyObservableService.STATE_IDLE

    def main(self):
        logging.getLogger().info("Starting main loop")

        timer = schedule.every(3).seconds
        timer.do(self.my_job)
        while self._is_running:
            schedule.run_pending()
            time.sleep(1)

    def my_job(self):
        logging.getLogger().info("Starting main job")

        logging.getLogger().debug("Setting busy state")
        self._state = MyObservableService.STATE_BUSY
        self.notifyObservers()
        logging.getLogger().info("Starting session...")
        time.sleep(15)
        logging.getLogger().debug("Finished. Switching back to idle state")
        self._state = MyObservableService.STATE_IDLE
        self.notifyObservers()


if __name__ == '__main__':
    MyObservableService.parse_command_line()
