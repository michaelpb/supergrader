import subprocess
import re
import os.path
import sys

import utils

INFINITY = sys.maxsize

class ConfigurationError(Exception):
    pass

class ValidationError(Exception):
    pass

class ValidationUnableToCheckError(Exception):
    pass

class ValidatorBase:
    def get_name(self):
        if hasattr(self, 'name'):
            return self.name
        return self.__class__.__name__

    def get_feedback(self):
        return None

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
                raise ConfigurationError('Invalid captures: %s' % str(captures))

            raise ConfigurationError('Captures not yet implemented')
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
            raise ValidationError('Could not find: ' + ', '.join(fails))

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


class FileTextValidator(ValidatorBase):
    regexp_whitespace = re.compile(r'\s+', re.MULTILINE)

    def get_fuzzy_text(self, directory):
        raise ValueError('not implemented yet')

    def get_regexp(self, directory):
        raise ValueError('not implemented yet')
        return None

    def get_text(self, directory):
        return self.text

    def get_range(self, directory):
        exact_count = getattr(self, 'exact_count', None)
        if exact_count:
            return range(exact_count, exact_count + 1)

        max_count = getattr(self, 'max_count', None)
        min_count = getattr(self, 'min_count', None)
        step_count = getattr(self, 'step_count', None)
        if not max_count and not min_count:
            return None

        if max_count:
            max_count += 1 # make inclusive
        else:
            max_count = INFINITY
        if min_count and step_count:
            return range(min_count, max_count, step_count)
        elif min_count:
            return range(min_count, max_count)
        else:
            return range(max_count)

    def get_count(self, directory):
        return getattr(self, 'count', None)

    def sanitize(self, text, is_search=False):
        if getattr(self, 'normalize_whitespace', False):
            text = re.sub(self.regexp_whitespace, ' ', text)
        if getattr(self, 'ignore_case', False):
            text = text.lower()
        if not is_search:
            if getattr(self, 'whole_word_only', False):
                text = text.split()
        return text

    def validate(self, directory):
        full_path = os.path.join(directory, self.path)
        if not os.path.exists(path):
            raise ValidationError(f'Expected file does not exist: {self.path}')
        file_contents = self.sanitize(open(full_path).read())
        text = self.get_text()
        sanitized_text = self.sanitize(text, is_search=True)
        if sanitized_text not in file_contents:
            raise ValidationError(f'{self.path} does not contain "{text}"')

        expected_range = self.get_range()
        if expected_range:
            actual_count = file_contents.count(sanitized_text)
            msg = f'{self.path} contains {actual_count} instances of {text}'
            if actual_count not in expected_range:
                if expected_range.stop == INFINITY:
                    msg += f'(instead of at least {actual_range.start}'
                else:
                    msg += f'(instead of between {actual_range.start} and {actual_range.stop}'
                if expected_range.step != 1:
                    msg += f', step {expected_range.step}'
                msg += ')'
                raise ValidationError(msg)


shell_validator = ShellValidator.as_function()
file_structure_validator = FileStructureValidator.as_function()
file_text_validator = FileTextValidator.as_function()

