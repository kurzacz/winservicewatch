import winservicewatch.Service


class MyObservableService(winservicewatch.Service.WinService):
    pass


if __name__ == '__main__':
    MyObservableService.parse_command_line()
