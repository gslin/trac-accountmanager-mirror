# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
# Copyright (C) 2015 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Matthew Good <trac@matt-good.net>

import sys
import unittest

_twill_required = 'Twill>=2'
try:
    import twill
except ImportError:
    twill = None
    INCLUDE_FUNCTIONAL_TESTS = False
else:
    # XXX Avoid tracenv log writing to stdout via twill.log
    if hasattr(twill, 'log') and hasattr(twill, 'handler'):
        twill.log.removeHandler(twill.handler)
    import pkg_resources
    try:
        pkg_resources.require(_twill_required)
    except:
        INCLUDE_FUNCTIONAL_TESTS = False
        twill = None
    else:
        INCLUDE_FUNCTIONAL_TESTS = True


def test_suite():
    from . import (admin, api, db, guard, htfile, model, register, svnserve,
                   util)
    from ..opt import tests as opt_tests

    suite = unittest.TestSuite()
    for mod in (admin, api, db, guard, htfile, model, register, svnserve, util,
                opt_tests):
        suite.addTest(mod.test_suite())

    if INCLUDE_FUNCTIONAL_TESTS:
        from . import functional
        suite.addTest(functional.test_suite())
    elif not twill:
        sys.stderr.write('SKIP: functional tests (%s unavailable)\n' %
                         _twill_required)
    else:
        sys.stderr.write('SKIP: functional tests\n')
    return suite


if __name__ == '__main__':
    if '--skip-functional-tests' in sys.argv:
        sys.argv.remove('--skip-functional-tests')
        INCLUDE_FUNCTIONAL_TESTS = False
    unittest.main(defaultTest='test_suite')
