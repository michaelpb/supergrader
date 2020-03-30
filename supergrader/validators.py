import subprocess

class ValidatorBase:
    pass

def apply_command_list_template(command_list, directory, args):
    '''
    Perform necessary substitutions on a command list to create a CLI-ready
    list to launch a validator process via system binary.
    '''
    replacements = {
        '$DIR': directory,
    }

    # Add in positional arguments ($0, $1, etc)
    for i, arg in enumerate(args):
        replacements['$' + str(i)] = arg

    results = [replacements.get(arg, arg) for arg in command_list]

    # Returns list of truthy replaced arguments in command
    return [item for item in results if item]


class ShellValidator(ValidatorBase):
    def get_arguments(self, resource):
        return []

    def get_kwds(self, directory):
        return {'shell': True}

    def get_cwd(self, directory):
        return directory

    def get_command(self, directory):
        return apply_command_list_template(
            self.command,
            directory,
            self.get_arguments(directory),
        )

    def get_capture(self, in_resource, out_resource):
        return []

    def _run_command(self, cmd, kwds, in_resource, out_resource):
        # Compute working directory and misc keyword args
        kwds.setdefault('cwd', self.get_cwd(in_resource, out_resource))

        # Run the command itself, capturing stdout and/or stderr as necessary
        captures = self.get_capture(in_resource, out_resource)
        if captures:
            if set(captures) - set(['stdout', 'stderr']):
                raise ValueError('Invalid captures: %s' % str(captures))
            output_file = out_resource.cache_path
            with open(output_file, 'w+') as fd:
                for capture in captures:
                    kwds[capture] = fd
                result = subprocess.run(cmd, **kwds)
        else:
            result = subprocess.run(cmd, **kwds)
        return result

    def validate_directory(self, directory):
        # Ensure directories are created and run the actual command
        cmd = self.get_command(directory)
        kwds = self.get_kwds(directory)
        result = self._run_command(cmd, kwds, directory)
        return result


class FileStructureValidator(ValidatorBase):
    pass

class ConditionalValidator(ValidatorBase):
    pass
