class TransferResult:
    def __init__(self, success: bool, message: str = "", error_code: int = None):
        self.success = success
        self.message = message
        self.error_code = error_code

    def __repr__(self):
        return f"TransferResult(success={self.success}, message='{self.message}', error_code={self.error_code})"