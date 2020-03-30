# Testing profile during development
from supergrader.validators import ShellValidator

class EchoValidator(ShellValidator):
    command = 'echo "Testing testing 123"'

VALIDATORS = [
    EchoValidator,
]

