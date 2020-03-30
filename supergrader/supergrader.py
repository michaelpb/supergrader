import argparse
import os
import sys
import importlib
import validators

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


def source_directories(args):
    '''
    Given parsed args, yield paths to all source directories
    '''
    for package_name in args.directories:
        yield os.path.join(args.source, package_name)


def munge_path(path):
    '''
    Replaces all files prefixed with '_' with ones prefixed with '.'
    '''
    return os.path.join(*[
        node if not node.startswith('_') else '.%s' % node[1:]
        for node in os.path.split(path)
    ])


def directory_walk(source_d, destination_d):
    '''
    Walk a directory structure and yield full parallel source and destination
    files, munging filenames as necessary
    '''
    for dirpath, dirnames, filenames in os.walk(source_d):
        relpath = os.path.relpath(dirpath, source_d).strip('./')
        for filename in filenames:
            suffix = filename
            if relpath:
                suffix = os.path.join(relpath, filename)
            full_source_path = os.path.join(source_d, suffix)
            full_destination_path = os.path.join(
                destination_d, munge_path(suffix))
            yield full_source_path, full_destination_path


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
        print('Loaded profile:', profile)
    return profile

def get_validator_classes(profile):
    print(dir(profile))
    return profile.VALIDATORS

def main(args):
    try:
        check_args(args)
        profile = get_profile(args)
        validator_classes = get_validator_classes(profile)
    except ArgError:
        parser.print_usage()
        sys.exit(1)

    # Args are correct, lets now perform necessary steps
    for source_d in args.directories:
        for validator_class in validator_classes:
            validator = validator_class()
            validator.validate_directory(source_d)


def cli():
    main(parse_args(sys.argv))


if __name__ == '__main__':
    cli()
