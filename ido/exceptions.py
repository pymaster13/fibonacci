
class IDOError(Exception):
    pass


class ExchangeAddError(IDOError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class CoinAddError(IDOError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class SmartcontractAddError(IDOError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class IDOExistsError(IDOError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class AllocationError(IDOError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)
