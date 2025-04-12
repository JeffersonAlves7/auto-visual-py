class AutoVisualException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class PathNotFoundError(AutoVisualException):
    def __init__(self, *args):
        super().__init__(*args)
