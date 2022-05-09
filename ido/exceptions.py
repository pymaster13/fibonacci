
class IDOError(Exception):
    pass


class ExchangeAddError(IDOError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)

