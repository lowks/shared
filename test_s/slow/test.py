import os
import s
import sys
import logging
import pytest


_keys = list(sys.modules.keys())


def setup_module():
    s.log.setup(level='debug', short=True, pprint=True)


def setup_function(fn):
    fn.ctx = s.shell.tempdir()
    fn.ctx.__enter__()
    for k, v in list(sys.modules.items()):
        if k not in _keys:
            del sys.modules[k]
    sys.path.insert(0, os.getcwd())

def teardown_function(fn):
    fn.ctx.__exit__(None, None, None)
    sys.path.pop(0)


def test_collect_tests():
    with open('foo.py', 'w') as fio:
        fio.write("""
def test1():
    pass
""")
    assert s.test._collect_tests('foo.py') == ["<Function 'test1'>"]


def test_climb():
    s.shell.run('mkdir -p 1/2/3 && touch 1/a 1/2/b 1/2/3/s')
    x = os.getcwd()
    with s.shell.cd('1/2/3'):
        assert list(s.test._climb())[0] == [os.path.join(x, '1/2/3'), [], ['s']]
        assert list(s.test._climb())[1] == [os.path.join(x, '1/2'), ['3'], ['b']]
        assert list(s.test._climb())[2] == [os.path.join(x, '1'), ['2'], ['a']]

def test_all_test_files():
    s.shell.run('mkdir -p .git test_foo/fast foo && touch test_foo/fast/bar.py foo/bar.py foo/__init__.py')
    assert s.test.all_test_files() == ['test_foo/fast/bar.py']


def test_all_code_files_and_python_packages():
    s.shell.run('mkdir -p .git foo && touch foo/bar.py foo/__init__.py')
    assert s.test._python_packages(os.walk('.')) == ['foo']
    assert set(s.test.all_code_files()) == {'foo/bar.py', 'foo/__init__.py'}


def test_test_fail():
    with open('test_foo.py', 'w') as fio:
        fio.write("""
def test1():
   x, y = 1, 3
   assert x == y
""")
    val = s.test._test('test_foo.py')
    assert val.result[-3].endswith("assert 1 == 3") # make sure we are getting the _pytest_insight output


def test_test_pass():
    with open('test_foo.py', 'w') as fio:
        fio.write("""
def test1():
   x, y = 1, 1
   assert x == y
""")
    assert not s.test._test('test_foo.py').result


def test_run_tests_once_fail():
    logging.info(os.getcwd())
    s.shell.run('mkdir .git')
    with s.shell.cd('test_foo/fast'):
        with open('test1.py', 'w') as fio:
            fio.write("""
def test1():
    pass
""")
        with open('test2.py', 'w') as fio:
            fio.write("""
def test2():
    1/0
""")
    s.shell.run('touch test_foo/__init__.py test_foo/fast/__init__.py')
    val = s.test.run_tests_once()
    assert len(val) == 3
    assert len([x for x in val if x.result]) == 1


def test_run_tests_once_pass():
    s.shell.run('mkdir .git')
    with s.shell.cd('test_foo/fast'):
        with open('test1.py', 'w') as fio:
            fio.write("""
def test1():
    pass
""")
        with open('test2.py', 'w') as fio:
            fio.write("""
def test2():
    pass
""")
    s.shell.run('touch test_foo/__init__.py test_foo/fast/__init__.py')
    assert [x.result for x in s.test.run_tests_once()] == [False, False, False]


def test_climb_git_root():
    with s.shell.tempdir():
        path = os.getcwd()
        s.shell.run('mkdir .git')
        with s.shell.cd('a/b/c'):
            assert path == s.fn.thread(
                s.test._climb(),
                s.test._git_root,
            )

s.hacks.decorate(globals(), __name__, s.fn.badfunc)