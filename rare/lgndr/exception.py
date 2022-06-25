class LgndrException(RuntimeError):
    def __init__(self, message="Error in Legendary"):
        self.message = message
        super(LgndrException, self).__init__(self.message)
