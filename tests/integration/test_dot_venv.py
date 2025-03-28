# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pipenv.utils.shell import normalize_drive, temp_environ


@pytest.mark.dotvenv
def test_venv_in_project(PipenvInstance):
    with temp_environ():
        os.environ['PIPENV_VENV_IN_PROJECT'] = '1'
        with PipenvInstance() as p:
            c = p.pipenv('install requests')
            assert c.returncode == 0
            assert normalize_drive(p.path) in p.pipenv('--venv').stdout


@pytest.mark.dotvenv
def test_venv_at_project_root(PipenvInstance):
    with temp_environ():
        with PipenvInstance(chdir=True) as p:
            os.environ['PIPENV_VENV_IN_PROJECT'] = '1'
            c = p.pipenv('install')
            assert c.returncode == 0
            assert normalize_drive(p.path) in p.pipenv('--venv').stdout
            del os.environ['PIPENV_VENV_IN_PROJECT']
            os.mkdir('subdir')
            os.chdir('subdir')
            # should still detect installed
            assert normalize_drive(p.path) in p.pipenv('--venv').stdout


@pytest.mark.dotvenv
def test_reuse_previous_venv(PipenvInstance):
    with PipenvInstance(chdir=True) as p:
        os.mkdir('.venv')
        c = p.pipenv('install requests')
        assert c.returncode == 0
        assert normalize_drive(p.path) in p.pipenv('--venv').stdout


@pytest.mark.dotvenv
@pytest.mark.parametrize('venv_name', ('test-venv', os.path.join('foo', 'test-venv')))
def test_venv_file(venv_name, PipenvInstance):
    """Tests virtualenv creation when a .venv file exists at the project root
    and contains a venv name.
    """
    with PipenvInstance(chdir=True) as p:
        file_path = os.path.join(p.path, '.venv')
        with open(file_path, 'w') as f:
            f.write(venv_name)

        with temp_environ(), TemporaryDirectory(
            prefix='pipenv-', suffix='temp_workon_home'
        ) as workon_home:
            os.environ['WORKON_HOME'] = workon_home
            if 'PIPENV_VENV_IN_PROJECT' in os.environ:
                del os.environ['PIPENV_VENV_IN_PROJECT']

            c = p.pipenv('install')
            assert c.returncode == 0

            c = p.pipenv('--venv')
            assert c.returncode == 0
            venv_loc = Path(c.stdout.strip()).absolute()
            assert venv_loc.exists()
            assert venv_loc.joinpath('.project').exists()
            venv_path = normalize_drive(venv_loc.as_posix())
            if os.path.sep in venv_name:
                venv_expected_path = Path(p.path).joinpath(venv_name).absolute().as_posix()
            else:
                venv_expected_path = Path(workon_home).joinpath(venv_name).absolute().as_posix()
            assert venv_path == normalize_drive(venv_expected_path)


@pytest.mark.dotvenv
def test_empty_venv_file(PipenvInstance):
    """Tests virtualenv creation when a empty .venv file exists at the project root
    """
    with PipenvInstance(chdir=True) as p:
        file_path = os.path.join(p.path, '.venv')
        with open(file_path, 'w'):
            pass

        with temp_environ(), TemporaryDirectory(
            prefix='pipenv-', suffix='temp_workon_home'
        ) as workon_home:
            os.environ['WORKON_HOME'] = workon_home
            if 'PIPENV_VENV_IN_PROJECT' in os.environ:
                del os.environ['PIPENV_VENV_IN_PROJECT']

            c = p.pipenv('install')
            assert c.returncode == 0

            c = p.pipenv('--venv')
            assert c.returncode == 0
            venv_loc = Path(c.stdout.strip()).absolute()
            assert venv_loc.exists()
            assert venv_loc.joinpath('.project').exists()
            from pathlib import PurePosixPath
            venv_path = normalize_drive(venv_loc.as_posix())
            venv_path_parent = str(PurePosixPath(venv_path).parent)
            assert venv_path_parent == Path(workon_home).absolute().as_posix()


@pytest.mark.dotvenv
def test_venv_file_with_path(PipenvInstance):
    """Tests virtualenv creation when a .venv file exists at the project root
    and contains an absolute path.
    """
    with temp_environ(), PipenvInstance(chdir=True) as p:
        with TemporaryDirectory(
            prefix='pipenv-', suffix='-test_venv'
        ) as venv_path:
            if 'PIPENV_VENV_IN_PROJECT' in os.environ:
                del os.environ['PIPENV_VENV_IN_PROJECT']

            file_path = os.path.join(p.path, '.venv')
            with open(file_path, 'w') as f:
                f.write(venv_path)

            c = p.pipenv('install')
            assert c.returncode == 0
            c = p.pipenv('--venv')
            assert c.returncode == 0
            venv_loc = Path(c.stdout.strip())

            assert venv_loc.joinpath('.project').exists()
            assert venv_loc == Path(venv_path)
