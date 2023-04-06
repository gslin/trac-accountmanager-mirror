# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Matthew Good <trac@matt-good.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Pedro Algarvio <ufs@ufsoft.org>

import os
import sys
import time
import socket
import subprocess

from trac.env import Environment
from trac.util.compat import close_fds
try:
    from trac.test import rmtree
except ImportError:
    from shutil import rmtree

from .smtpd import SMTPThreadedServer


TOX_ENV_DIR = os.environ.get('TOX_ENV_DIR')


if hasattr(subprocess.Popen, '__enter__'):
    Popen = subprocess.Popen
else:
    class Popen(subprocess.Popen):

        def __enter__(self):
            return self

        def __exit__(self, *args):
            try:
                if self.stdin:
                    self.stdin.close()
            finally:
                self.wait()
            for f in (self.stdout, self.stderr):
                if f:
                    f.close()


def get_topdir():
    path = os.path.dirname(os.path.abspath(__file__))
    suffix = '/acct_mgr/tests/functional'.replace('/', os.sep)
    if not path.endswith(suffix):
        raise RuntimeError("%r doesn't end with %r" % (path, suffix))
    return path[:-len(suffix)]


def get_testdir():
    dir_ = TOX_ENV_DIR
    if dir_ and os.path.isdir(dir_):
        dir_ = os.path.join(dir_, 'tmp')
    else:
        dir_ = get_topdir()
    if not os.path.isabs(dir_):
        raise RuntimeError('Non absolute directory: %s' % repr(dir_))
    return os.path.join(dir_, 'testenv')


def get_ephemeral_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', 0))
        s.listen(1)
        return s.getsockname()[1]
    finally:
        s.close()


def to_b(value):
    if isinstance(value, unicode):
        return value.encode('utf-8')
    if isinstance(value, bytes):
        return value
    raise ValueError(type(value))


class TestEnvironment(object):

    _testdir = get_testdir()
    _plugins_dir = os.path.join(_testdir, 'plugins') if not TOX_ENV_DIR else ''
    _devnull = None
    _log = None
    port = None
    smtp_port = None
    tracdir = None
    url = None
    smtpd = None
    _env = None
    _tracd = None

    def __init__(self):
        if os.path.isdir(self._testdir):
            rmtree(self._testdir)
        os.mkdir(self._testdir)
        if self._plugins_dir:
            os.mkdir(self._plugins_dir)

    _inherit_template = """\
[inherit]
plugins_dir = %(plugins_dir)s
[logging]
log_type = file
log_level = INFO
[trac]
base_url = %(url)s
use_chunked_encoding = disabled
[project]
url = %(url)s
admin = testenv%(port)d@localhost
[notification]
smtp_enabled = enabled
smtp_from = testenv%(port)d@localhost
smtp_port = %(smtp_port)d
smtp_server = localhost
"""

    @property
    def inherit_file(self):
        return self._inherit_template % \
               {'plugins_dir': self._plugins_dir, 'url': self.url,
                'port': self.port, 'smtp_port': self.smtp_port}

    def init(self):
        self._devnull = os.open(os.devnull, os.O_RDWR)
        self._log = os.open(os.path.join(self._testdir, 'tracd.log'),
                            os.O_WRONLY | os.O_CREAT | os.O_APPEND)
        self.port = get_ephemeral_port()
        self.smtp_port = get_ephemeral_port()
        if self._plugins_dir:
            self.check_call([sys.executable, 'setup.py', 'develop', '-mxd',
                             self._plugins_dir])
        self.tracdir = os.path.join(self._testdir, 'trac')
        self.url = 'http://127.0.0.1:%d/%s' % \
                   (self.port, os.path.basename(self.tracdir))
        inherit = os.path.join(self._testdir, 'inherit.ini')
        with open(inherit, 'w') as f:
            f.write(self.inherit_file)
        args = [sys.executable, '-m', 'trac.admin.console', self.tracdir]
        with self.popen(args, stdin=subprocess.PIPE) as proc:
            proc.stdin.write(
                b'initenv --inherit=%s testenv%d sqlite:db/trac.db\n'
                b'config set components acct_mgr.* enabled\n'
                b'config set components trac.web.auth.loginmodule disabled\n'
                % (to_b(inherit), self.port))
        self.smtpd = SMTPThreadedServer(self.smtp_port)
        self.smtpd.start()
        self.start()

    def cleanup(self):
        self.stop()
        if self.smtpd:
            self.smtpd.stop()
            self.smtpd = None
        if self._env:
            self._env.shutdown()
            self._env = None
        if self._devnull is not None:
            os.close(self._devnull)
            self._devnull = None
        if self._log is not None:
            os.close(self._log)
            self._log = None

    def start(self):
        if self._tracd and self._tracd.returncode is None:
            raise RuntimeError('tracd is running')
        args = [
            sys.executable, '-m', 'trac.web.standalone',
            '--port=%d' % self.port, '--hostname=localhost', self.tracdir,
        ]
        self._tracd = self.popen(args, stdout=self._log, stderr=self._log)
        start = time.time()
        while time.time() - start < 10:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect(('127.0.0.1', self.port))
            except socket.error:
                time.sleep(0.125)
            else:
                break
            finally:
                s.close()
        else:
            raise RuntimeError('Timed out waiting for tracd to start')

    def stop(self):
        if self._tracd:
            try:
                self._tracd.terminate()
            except EnvironmentError:
                pass
            self._tracd.wait()
            self._tracd = None

    def restart(self):
        self.stop()
        self.start()

    def popen(self, *args, **kwargs):
        kwargs.setdefault('stdin', self._devnull)
        kwargs.setdefault('stdout', self._devnull)
        kwargs.setdefault('stderr', self._devnull)
        kwargs.setdefault('close_fds', close_fds)
        return Popen(*args, **kwargs)

    def check_call(self, *args, **kwargs):
        kwargs.setdefault('stdin', self._devnull)
        kwargs.setdefault('stdout', subprocess.PIPE)
        kwargs.setdefault('stderr', subprocess.PIPE)
        with self.popen(*args, **kwargs) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError('Exited with %d (stdout %r, stderr %r)' %
                                   (proc.returncode, stdout, stderr))

    def get_trac_environment(self):
        if not self._env:
            self._env = Environment(self.tracdir)
        return self._env

    def _tracadmin(self, *args):
        self.check_call((sys.executable, '-m', 'trac.admin.console',
                         self.tracdir) + args)
