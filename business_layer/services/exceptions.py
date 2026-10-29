"""Lỗi nghiệp vụ được ném bởi các service không phụ thuộc framework."""


class BusinessError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)
