import argparse
import os
import sys
import importlib
import traceback

# 1st party
import validators
import utils

_is_verbose = False
parser = None

class ArgError(ValueError):
    pass

def parse_args(argv):
    global parser
    parser = argparse.ArgumentParser(
        prog='supergrader',
        description='Symlink files recursively, good for dotfiles.'
    )
    supergrader_profile = os.environ.get('SUPERGRADER_PROFILE', 'sgprofile')

    parser.add_argument('-v', '--verbose', help='increase output verbosity',
                        action='store_true')
    parser.add_argument('-p', '--profile', default=supergrader_profile,
                        help='Python module path to "profile" module')
    parser.add_argument('directories', nargs='*',
                        help='one or more activity or assignment directories')
    args = parser.parse_args(argv)
    if sys.argv[0] in args.directories:
        args.directories.remove(sys.argv[0])
    return args


def check_args(args):
    '''
    Raises value errors if args is missing something
    '''
    if not args.directories:
        raise ArgError()
    if args.verbose:
        global _is_verbose
        _is_verbose = True
    # Expand all relevant user directories
    #args.source = os.path.expanduser(args.source)

def get_profile(args):
    sys.path.append(os.getcwd())
    profile = importlib.import_module(args.profile)
    if not profile:
        print('Unable to import profile. Stopping.')
        raise ArgError()
    if _is_verbose:
        utils.trace('Loaded profile:', repr(profile))
    return profile

def get_validator_classes(profile):
    return profile.VALIDATORS

def main(args):
    try:
        check_args(args)
        profile = get_profile(args)
        validator_classes = get_validator_classes(profile)
    except ArgError:
        parser.print_usage()
        sys.exit(1)

    results_grid = {}
    results_list = []

    # Args are correct, lets now perform necessary steps
    for source_d in args.directories:
        if _is_verbose:
            utils.trace('TARGET', source_d)
        info = {
            'directory': source_d,
            'errors': 0,
            'successes': 0,
            'failures': 0,
            'skipped': 0,
            'messages': {
                'error': [],
                'skip': [],
                'fail': [],
                'feedback': [],
            },
        }
        results_list.append(info)
        for validator_class in validator_classes:

            # Check if validator class is actually a list or tuple that
            # consists of the name of the function, and keyword args
            if hasattr(validator_class, '__iter__'):
                name, kwargs = validator_class
                if hasattr(validators, name + '_validator'):
                    name = name + '_validator'
                validator_function = getattr(validators, name)
                validator_class = validator_function(**kwargs)

            validator = validator_class()
            name = validator.get_name()

            if _is_verbose:
                utils.trace('Validator', name)

            # Actually run the validator, catching exceptions to mark as
            # failure
            result = '.'
            try:
                validator.validate(source_d)
            except validators.ValidationUnableToCheckError as e:
                if _is_verbose:
                    utils.failure(source_d, name)
                info['skipped'] += 1
                info['messages']['skip'].append(str(e))
                result = '?'
            except validators.ValidationError as e:
                if _is_verbose:
                    utils.failure(source_d, name)
                info['failures'] += 1
                result = 'F'
                info['messages']['fail'].append(str(e))
            except Exception as e:
                if _is_verbose:
                    utils.failure(source_d, name)
                info['failures'] += 1
                info['errors'] += 1
                result = 'E'
                traceback.print_exc()
                info['messages']['error'].append(str(e))
            else:
                info['successes'] += 1
                feedback = validator.get_feedback()
                if feedback:
                    info['messages']['feedback'].append(feedback)
                if _is_verbose:
                    utils.success(source_d, name)

            # Set the result to results_grid
            key = format_matrix_labels(source_d, name)
            results_grid[key] = result


        if _is_verbose:
            if not info['failures']:
                utils.success(source_d, successes)
            else:
                utils.success(source_d, successes)
                utils.failure(source_d + ' failures:', failures)
                utils.failure(source_d + ' errors:', errors)
    print_report(results_grid, results_list)


def format_matrix_labels(source_d, name):
    dirname = source_d.strip('/')
    return dirname, name


def print_report(results_grid, results_list):
    for result in results_list:
        if result['failures'] + result['skipped']:
            print_result(**result)
        elif _is_verbose:
            print_result(**result)
    s = utils.format_matrix(results_grid)
    print(s)

def print_result(directory, errors, successes, failures, skipped, messages):
    print(
        utils.Term.Bold(directory),
        '-',
        utils.Term.Green(successes),
        utils.Term.Red(failures),
        utils.Term.Yellow(skipped),
    )

    for category, message_list in messages.items():
        if message_list:
            print(' ' * 4 + '[' + category.upper() + ']')
            for msg in message_list:
                print(' ' * 8 + '-', msg)

def cli():
    main(parse_args(sys.argv))


if __name__ == '__main__':
    cli()
