
class AccountError(Exception):
    pass


class EmptyTelegramNickError(AccountError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class UserWithTgExistsError(AccountError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class EmailValidationError(AccountError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class TgAccountVerifyError(AccountError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class InviterUserError(AccountError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class LoginUserError(AccountError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class UserDoesNotExists(AccountError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)


class TokenDoesNotExists(AccountError):
    def __init__(self, error) -> None:
        self.error = error
        super().__init__(error)