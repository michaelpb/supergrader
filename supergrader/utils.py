import sys

#
# Terminal output functions
# A few old ass functions for making output to the terminal neater
class Term:
    bold = "\033[1m"
    reset= "\033[0;0m"
    purple = '\033[95m'
    blue = '\033[94m'
    green = '\033[92m'
    yellow = '\033[93m'
    red = '\033[91m'
    Bold = staticmethod(lambda s: Term.bold + str(s) + Term.reset)
    Blue = staticmethod(lambda s: Term.blue + str(s) + Term.reset)
    Yellow = staticmethod(lambda s: Term.yellow + str(s) + Term.reset)
    Green = staticmethod(lambda s: Term.green + str(s) + Term.reset)
    Red = staticmethod(lambda s: Term.red + str(s) + Term.reset)
    Purple = staticmethod(lambda s: Term.purple + str(s) + Term.reset)

def warning(msg):
    sys.stderr.write(Term.Yellow("Warning: ") + Term.Bold(msg) + "\n")

def trace(msg, arg=''):
    sys.stdout.write(Term.Blue("---> ") + msg + ((" "+Term.Purple(arg)) if arg else '') + "\n")

def success(msg, arg=''):
    sys.stdout.write(Term.Green('[X] SUCCESS ') + msg + ((" "+Term.Purple(arg)) if arg else '') + "\n")

def failure(msg, arg=''):
    sys.stdout.write(Term.Red('[ ] FAIL   ') + msg + ((" "+Term.Purple(arg)) if arg else '') + "\n")

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


def make_matrix(labels_top, labels_side, matrix, max_width=80):
    results = []

    first_col_width = max(len(s) for s in labels_side) + 1
    column_labels = [' ' * first_col_width] + [s + ' ' for s in labels_top]

    total = sum(len(s) for s in column_labels)
    compressed_mode = total > max_width

    if compressed_mode:
        column_labels = []
        for index, label in enumerate(labels_top):
            number = '%02i' % i
            results.append(number + ' - ' + label)
            column_labels.append(results)

    column_widths = [len(s) for s in column_labels]
    results.append(''.join(column_labels))

    for i, row in enumerate(matrix):
        row_formatted = []
        row = [labels_side[i]] + row
        for width, col in zip(column_widths, row):
            row_formatted.append(col.ljust(width))
        results.append(''.join(row_formatted))

    return '\n'.join(results)


def tuple_dict_to_display_matrix(tuple_dict):
    # Remove duplicates, sort, and split the left and right column labels
    left_labels = sorted(list(set(left for left, _ in tuple_dict.keys())))
    right_labels = sorted(list(set(right for _, right in tuple_dict.keys())))

    # Build the matrix "list of lists" format for the tuple_dict
    matrix = [
        [tuple_dict.get((left, right)) for left in left_labels]
        for right in right_labels
    ]
    return left_labels, right_labels, matrix


def format_matrix(tuple_dict):
    left_labels, right_labels, matrix = tuple_dict_to_display_matrix(tuple_dict)
    return make_matrix(left_labels, right_labels, matrix)


def error(msg):
    sys.stderr.write(
            Term.Red(sys.argv[0]) + ": " +
            Term.Red("Error") + ": " +
            Term.Bold(msg) + "\n")
    sys.exit(1)


def ___old_code(tuple_dict):
    matrix = []
    left_labels = set(left for left, right in tuple_dict.keys())
    right_labels = set(right for left, right in tuple_dict.keys())
    left_labels_list = list(left_labels)
    right_labels_list = list(right_labels)

    matrix = [
        [None for i in range(len(left_labels))]
        for i in range(len(right_labels))
    ]

    for (left, right), key in tuple_dict.items():
        left_index = left_labels_list.index(left)
        right_index = right_labels_list.index(left)
        matrix[right_index][left_index] = key
    return matrix

