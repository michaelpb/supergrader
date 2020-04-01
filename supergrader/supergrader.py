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

    parser.add_argument('-v', '--verbose', help='increase output verbosity',
                        action='store_true')
    parser.add_argument('-p', '--profile', default='sgprofile',
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

    results = {}

    # Args are correct, lets now perform necessary steps
    for source_d in args.directories:
        if _is_verbose:
            utils.trace('TARGET', source_d)
        failures = 0
        errors = 0
        successes = 0
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
                successes += 1
            except validators.ValidationUnableToCheckError as e:
                utils.failure(source_d, name)
                failures += 1
                result = '?'
            except validators.ValidationError as e:
                utils.failure(source_d, name)
                failures += 1
                result = 'F'
                print(e)
            except Exception as e:
                utils.failure(source_d, name)
                failures += 1
                errors += 1
                result = 'E'
                traceback.print_exc()
            else:
                if _is_verbose:
                    utils.success(source_d, name)

            # Set the result to results
            key = format_matrix_labels(source_d, name)
            results[key] = result

        if _is_verbose:
            if not failures + errors:
                utils.success(source_d, successes)
            else:
                utils.success(source_d, successes)
                utils.failure(source_d + ' failures:', failures)
                utils.failure(source_d + ' errors:', errors)
    print_report(results)


def format_matrix_labels(source_d, name):
    dirname = source_d.strip('/')
    return dirname, name


def print_report(results):
    s = utils.format_matrix(results)
    print(s)

def cli():
    main(parse_args(sys.argv))


if __name__ == '__main__':
    cli()
