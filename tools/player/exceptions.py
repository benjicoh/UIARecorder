class PlayerException(Exception):
    """Base exception for the player."""
    pass

class TestCaseNotFound(PlayerException):
    """Raised when the TestCase class is not found in a script."""
    pass

class InvalidTestCase(PlayerException):
    """Raised when the TestCase class does not inherit from BaseTestCase."""
    pass
