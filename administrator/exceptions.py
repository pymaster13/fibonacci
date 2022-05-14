
class AdminError(Exception):
    pass


class GrantPermissionsError(AdminError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class IncorrectDateError(AdminError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)
