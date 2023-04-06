# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Jun Omae <jun66j5@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

from trac.test import EnvironmentStub

from ..http import HttpAuthStore


class HttpAuthTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=[HttpAuthStore])
        self.store = HttpAuthStore(self.env)

    def test_get_users(self):
        self.assertEqual([], self.store.get_users())

    def test_has_user(self):
        self.assertEqual(False, self.store.has_user('anonymous'))
        self.assertEqual(False, self.store.has_user('admin'))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HttpAuthTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
