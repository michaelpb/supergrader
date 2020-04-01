import subprocess
import os.path

import utils

class ValidationError(Exception):
    pass

class ValidationUnableToCheckError(Exception):
    pass

class ValidatorBase:
    def get_name(self):
        if hasattr(self, 'name'):
            return self.name
        return self.__class__.__name__

    @classmethod
    def as_function(cls):
        '''
        Use to create less-verbose function-based syntax for creating and using
        validators
        '''
        def validator_as_function(**kwargs):
            # Default name of validator to parent validator class name
            kwargs.setdefault('name', cls.__name__)

            class SubclassedValidator(cls):
                pass

            for key, value in kwargs.items():
                setattr(SubclassedValidator, key, value)

            return SubclassedValidator
        return validator_as_function


class ShellValidator(ValidatorBase):
    def get_arguments(self, resource):
        return []

    def get_kwds(self, directory):
        return {'shell': True}

    def get_cwd(self, directory):
        return directory

    def get_command(self, directory):
        return utils.apply_command_list_template(
            self.command,
            directory,
            self.get_arguments(directory),
        )

    def get_capture(self, directory):
        return []

    def check_results(self, result):
        return result.returncode == 0

    def _run_command(self, cmd, kwds, directory):
        # Compute working directory and misc keyword args
        kwds.setdefault('cwd', self.get_cwd(directory))

        # Run the command itself, capturing stdout and/or stderr as necessary
        captures = self.get_capture(directory)
        if captures:
            if set(captures) - set(['stdout', 'stderr']):
                raise ValueError('Invalid captures: %s' % str(captures))

            raise ValueError('Captures not yet implemented')
            for capture in captures:
                kwds[capture] = fd
            result = subprocess.run(cmd, **kwds)
        else:
            result = subprocess.run(cmd, **kwds)
        return result

    def validate(self, directory):
        # Ensure directories are created and run the actual command
        cmd = self.get_command(directory)
        kwds = self.get_kwds(directory)
        result = self._run_command(cmd, kwds, directory)

        if not self.check_results(result):
            raise ValidationError('Command unsuccessful: ' + ' '.join(result.args))



class FileStructureValidator(ValidatorBase):
    example_dir_tree = [
        'file',
        ('dirname', [
            '',
        ])
    ]

    def get_dir_tree(self):
        return self.dir_tree

    def validate(self, directory):
        dir_tree = self.get_dir_tree()
        fails = []
        self._recurse_validate(dir_tree, directory, fails)
        if fails:
            raise ValidationError('Could not find: ' + ' '.join(fails))

    def _recurse_validate(self, dir_tree_node, root_dir, fails):
        if isinstance(dir_tree_node, str):
            path = os.path.join(root_dir, dir_tree_node)
            if not os.path.exists(path):
                fails.append(dir_tree_node)
        elif isinstance(dir_tree_node, list):
            for child in dir_tree_node:
                self._recurse_validate(child, root_dir, fails)
        else:
            path, children = dir_tree_node
            path = os.path.join(root_dir, path)
            if os.path.exists(path):
                self._recurse_validate(children, path, fails)
            else:
                fails.append(path)

shell_validator = ShellValidator.as_function()
file_structure_validator = FileStructureValidator.as_function()

