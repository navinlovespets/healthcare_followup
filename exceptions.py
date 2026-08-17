class ETLException(Exception):
    def __init__(self, stage, message):
        self.stage = stage
        super().__init__(message)