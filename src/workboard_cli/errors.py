class WorkboardError(Exception):
    def __init__(self, code, message, action=None):
        self.code = code
        self.message = message
        self.action = action
        super().__init__(message)

    def to_dict(self):
        d = {"code": self.code, "message": self.message}
        if self.action:
            d["action"] = self.action
        return d
