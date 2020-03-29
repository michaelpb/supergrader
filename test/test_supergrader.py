'''
Tests for `supergrader` module.
'''
import os
from os.path import join, exists
import pytest
import tempfile

from supergrader import supergrader


class BlankEnvironBase:
    @classmethod
    def setup_class(cls):
        # Save & delete
        cls.original_source = os.environ.get('SUPERGRADER_SOURCE')
        if cls.original_source is not None:
            del os.environ['SUPERGRADER_SOURCE']

    @classmethod
    def teardown_class(cls):
        # Restore environmental variables
        if cls.original_source is not None:
            os.environ['SUPERGRADER_SOURCE'] = cls.original_source


class TestParseArgs(BlankEnvironBase):
    def test_parse_args_default(self):
        args = supergrader.parse_args([])
        assert args.packages == []
        assert args.source == '~/dotfiles'
        assert args.destination == '~'
        assert args.backup == '~/.config/supergrader/backup/'
        assert not args.dryrun
        assert not args.verbose
        assert not args.skip_backup

    def test_parse_args_all(self):
        args = supergrader.parse_args([
            '-d', 'dest',
            '-s', 'src',
            '-b', 'backup',
            '--dryrun',
            '--verbose',
            '--skip-backup',
            'pkg1',
            'pkg2',
            'pkg3',
        ])
        assert args.packages == ['pkg1', 'pkg2', 'pkg3']
        assert args.source == 'src'
        assert args.destination == 'dest'
        assert args.backup == 'backup'
        assert args.dryrun
        assert args.verbose
        assert args.skip_backup

    def test_environ_defaults(self):
        os.environ['supergrader'] = 'src'
        os.environ['supergrader'] = 'dest'
        os.environ['supergrader'] = 'bup'
        args = supergrader.parse_args([])
        assert args.source == 'src'
        assert args.destination == 'dest'
        assert args.backup == 'bup'
        del os.environ['supergrader']
        del os.environ['supergrader']
        del os.environ['supergrader']

    def test_check_args(self):
        args = supergrader.parse_args([])
        with pytest.raises(ValueError):
            supergrader.check_args(args)
        args = supergrader.parse_args(['-s', '~/stuff', '-v', 'pkg'])
        supergrader.check_args(args)
        assert supergrader._is_verbose

        # ensure expands home
        assert (
            'home' in args.source or  # linux
            'Users' in args.source    # macOS
        )

    def test_arg_source_directories(self):
        args = supergrader.parse_args([
            '--source', 'src',
            '--dest', 'dest',
            'pkg1',
            'pkg2',
        ])
        dirs = list(supergrader.source_directories(args))
        assert dirs == ['src/pkg1', 'src/pkg2']


def write_tmp_file(path):
    try:
        os.makedirs(os.path.dirname(path))
    except OSError:
        pass
    open(path, 'w+').write('%s contents' % path)


def gen_tmp_files(root, files):
    for fn in files:
        write_tmp_file(join(root, fn))


def clear_tmp_files(root, files):
    for fn in files:
        path = join(root, fn)
        if exists(path):
            os.remove(path)
        try:
            os.removedirs(os.path.dirname(path))
        except OSError:
            pass


class TestPathGenerators:
    FILES = [
        '_vimrc',
        '_config/openbox/openbox.xml',
    ]

    @classmethod
    def setup_class(cls):
        cls.dir = tempfile.mkdtemp(prefix='tmp_supergrader_test_')
        gen_tmp_files(cls.dir, cls.FILES)
        cls.results = set([
            (join(cls.dir, '_vimrc'),
                join('test_out', '.vimrc')),
            (join(cls.dir, '_config/openbox/openbox.xml'),
                join('test_out', '.config/openbox/openbox.xml')),
        ])

    @classmethod
    def teardown_class(cls):
        clear_tmp_files(cls.dir, cls.FILES + ['.vimrc'])

    def test_directory_walk(self):
        results = list(supergrader.directory_walk(self.dir, 'test_out'))
        results_set = set(results)
        assert len(results_set) == len(results)  # ensure no dupes
        assert results_set == self.results

    def test_needed_symlink_walk(self):
        results = list(supergrader.needed_symlink_walk(self.dir, 'test_out'))
        results_set = set(results)
        assert len(results_set) == len(results)  # ensure no dupes
        assert results_set == self.results

    def test_partially_needed_symlink_walk(self):
        os.symlink(__file__, join(self.dir, '.vimrc'))
        results = list(supergrader.needed_symlink_walk(self.dir, self.dir))
        results_set = set(results)
        assert len(results_set) == len(results)  # ensure no dupes
        assert results_set == set([
            (join(self.dir, '_config/openbox/openbox.xml'),
                join(self.dir, '.config/openbox/openbox.xml')),
        ])


class TestFullBehavior:
    FILES = [
        '_vimrc',
        '_config/openbox/openbox.xml',
    ]

    def setup_method(self, method):
        self.dir = tempfile.mkdtemp(prefix='tmp_supergader_test_IN_')
        self.out_dir = tempfile.mkdtemp(prefix='tmp_supergader_test_OUT_')
        gen_tmp_files(join(self.dir, 'vim'), self.FILES)

    def teardown_method(self, method):
        clear_tmp_files(join(self.dir, 'vim'), self.FILES)
        clear_tmp_files(self.out_dir, self.FILES)

    def test_main(self):
        args = supergrader.parse_args([
            '--source', self.dir,
            '--destination', self.out_dir,
            '--backup', join(self.dir, 'path/to/bup'),
            'vim',
        ])
        supergrader.main(args)
        assert exists(join(self.out_dir, '.vimrc'))
        assert exists(join(self.out_dir, '.config', 'openbox', 'openbox.xml'))
        contents = open(join(self.out_dir, '.vimrc')).read()
        assert contents == '%s contents' % join(self.dir, 'vim', '_vimrc')

    def test_backup(self):
        args = supergrader.parse_args([
            '--source', self.dir,
            '--destination', self.out_dir,
            '--backup', join(self.dir, 'path/to/bup'),
            'vim',
        ])
        open(join(self.out_dir, '.vimrc'), 'w+').write('original')
        supergrader.main(args)
        assert exists(join(self.out_dir, '.vimrc'))
        assert exists(join(self.out_dir, '.config', 'openbox', 'openbox.xml'))
        assert exists(join(self.dir, 'path', 'to', 'bup', '.vimrc'))
        contents = open(join(self.dir, 'path', 'to', 'bup', '.vimrc')).read()
        assert contents == 'original'
        contents = open(join(self.out_dir, '.vimrc')).read()
        assert contents == '%s contents' % join(self.dir, 'vim', '_vimrc')
