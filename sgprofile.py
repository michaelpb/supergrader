# Testing profile during development
import supergrader
print(dir(supergrader))

class EchoValidator(supergrader.validators.ShellValidator):
    command = [
        'echo "Testing testing 123"',
    ]

VALIDATORS = [
    EchoValidator,
]

