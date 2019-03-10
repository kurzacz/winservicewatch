import logging
# TODO: Create requirements and put schedule
import schedule
import time
import winservicewatch.Service


class MyObservableService(winservicewatch.Service.WinService):

    def main(self):
        logging.getLogger().info("Starting main loop")

        timer = schedule.every(3).seconds
        timer.do(self.my_job)
        while self._is_running:
            schedule.run_pending()
            time.sleep(1)


if __name__ == '__main__':
    MyObservableService.parse_command_line()
