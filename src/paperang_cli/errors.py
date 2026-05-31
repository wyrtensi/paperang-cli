"""Project-specific exceptions and exit codes."""


class PaperangCliError(Exception):
    def __init__(self, message, *, code="CLI_ERROR", exit_code=1):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code


class ConfigError(PaperangCliError):
    def __init__(self, message):
        super().__init__(message, code="CONFIG_ERROR", exit_code=2)


class DriverError(PaperangCliError):
    def __init__(self, message):
        super().__init__(message, code="DRIVER_ERROR", exit_code=3)


class PrinterNotFoundError(DriverError):
    def __init__(self, message):
        super().__init__(message)
        self.code = "PRINTER_NOT_FOUND"
        self.exit_code = 4


class SafetyError(PaperangCliError):
    def __init__(self, message):
        super().__init__(message, code="SAFETY_ERROR", exit_code=5)