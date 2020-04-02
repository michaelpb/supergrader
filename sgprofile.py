# Testing profile during development
import supergrader
v = supergrader.validators

class DummyValidator(supergrader.validators.ShellValidator):
    command = [
        'exit 0',
    ]

VALIDATORS = [
    v.shell_validator(command=['exit 0'], name='Success Validator'),
    v.file_structure_validator(dir_tree=['__init__.py'], name='Has Init.py'),
    v.file_structure_validator(dir_tree=['supergrader.py'], name='has supergrader.py'),
    v.file_text_validator(text='def', min_count=12, max_count=200, path='supergrader.py', name='has def'),
    DummyValidator,
]

