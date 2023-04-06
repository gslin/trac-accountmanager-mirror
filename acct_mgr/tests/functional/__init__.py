# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Matthew Good <trac@matt-good.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Pedro Algarvio <ufs@ufsoft.org>

import io
import os
import unittest

import twill
try:
    import tidylib
except ImportError:
    tidylib = None


class TwillCommands(object):

    def __init__(self, commands):
        self.commands = commands
        self.browser = commands.browser

    def __getattr__(self, name):
        value = getattr(self.commands, name)
        if not callable(value):
            return value

        def wrapper(*args, **kwargs):
            prev = self.browser.result
            try:
                try:
                    return value(*args, **kwargs)
                finally:
                    result = self.browser.result
                    if result is not prev and 200 <= result.http_code < 300:
                        self.commands.tidy_ok()
            except twill.errors.TwillException as e:
                testname = _state.testname
                if not testname:
                    raise
                filename = os.path.join(_state.testenv.tracdir, 'log',
                                        testname + '.html')
                html = self.browser.html
                with io.open(filename, 'w', encoding='utf-8') as f:
                    f.write(html)
                raise twill.errors.TwillAssertionError('%s at %s' %
                                                       (e, filename))

        return wrapper


tc = TwillCommands(twill.commands)
if tidylib:
    twill.commands.config('require_tidy', 1)
    twill.commands.config('tidy_show_warnings', 'no')


class FunctionalTestState(object):

    testenv = None
    tester = None
    testname = None


_state = FunctionalTestState()


class FunctionalTestSuite(unittest.TestSuite):

    def run(self, result):
        if _state.testenv:
            testenv = None
        else:
            from .testenv import TestEnvironment
            from .tester import FunctionalTester
            testenv = TestEnvironment()
            testenv.init()
            _state.testenv = testenv
            _state.tester = FunctionalTester(testenv.url)
        try:
            return super(FunctionalTestSuite, self).run(result)
        finally:
            if testenv:
                testenv.cleanup()


class FunctionalTestCaseSetup(unittest.TestCase):

    @property
    def _testenv(self):
        return _state.testenv

    @property
    def _tester(self):
        return _state.tester

    @property
    def _smtpd(self):
        return _state.testenv.smtpd

    def setUp(self):
        _state.testname = self.__class__.__name__

    def tearDown(self):
        _state.testname = None


def test_suite():
    from . import testcases
    return testcases.test_suite()


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
