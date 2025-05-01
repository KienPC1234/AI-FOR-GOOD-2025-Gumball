
class GumballException(Exception):
    """
    The default gumball app's exception. Do not disclose any private information here as it will
    be used for generating error messages.
    """
    pass

class InvalidActionError(GumballException):
    """
    Exceptions for user's invalid actions.
    """
    pass

class DiskOperationError(GumballException):
    """
    Gumball disk-related error
    """
    pass

class UserTaskException(GumballException):
    """
    Exception for user tasks
    """
    pass

class AITaskException(UserTaskException):
    """
    AI task processing exception
    """
    pass

class ImageProcessingError(UserTaskException):
    """
    Image processing error
    """
    pass