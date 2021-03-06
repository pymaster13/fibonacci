
class CoreError(Exception):
    pass


class MetamaskWalletExistsError(CoreError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class AdminWalletIsEmptyError(CoreError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class CommissionError(CoreError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)
