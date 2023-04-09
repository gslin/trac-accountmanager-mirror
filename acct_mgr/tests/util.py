# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Steffen Hoffmann <hoff.st@web.de>

import unittest
from datetime import datetime

from trac.util.html import Fragment, tag

from ..compat import unicode
from ..util import i18n_tag, format_timespan, remove_zwsp


class UtilTestCase(unittest.TestCase):

    def test_format_timespan(self):
        self.assertEqual(format_timespan(0), '')
        self.assertEqual(format_timespan(1), '1 second')
        self.assertEqual(format_timespan(2), '2 seconds')
        self.assertEqual(format_timespan(119), '119 seconds')
        self.assertEqual(format_timespan(120), '00:02:00')
        self.assertEqual(format_timespan(86399), '23:59:59')
        self.assertEqual(format_timespan(86400), '1 day')
        self.assertEqual(format_timespan(86400 + 1), '1 day 1 second')
        d42 = 86400 * 42
        self.assertEqual(format_timespan(d42 - 1), '41 days 23:59:59')
        self.assertEqual(format_timespan(d42), '42 days')
        self.assertEqual(format_timespan(d42 + 119), '42 days 119 seconds')
        self.assertEqual(format_timespan(d42 + 120), '42 days 00:02:00')
        self.assertEqual(format_timespan(d42 + 86399), '42 days 23:59:59')

    def test_remove_zwsp(self):
        self.assertEqual(u'user', remove_zwsp(u'user'))
        self.assertEqual(u'user', remove_zwsp(u'\u200buser\u200b'))
        self.assertEqual(u'user', remove_zwsp(u'\u200fu\ufe00ser\u061c'))
        self.assertEqual(u'u\U000e00ffser', remove_zwsp(u'u\U000e00ffser'))
        self.assertEqual(u'user', remove_zwsp(u'u\U000e0100ser'))
        self.assertEqual(u'user', remove_zwsp(u'u\U000e01efser'))
        self.assertEqual(u'u\U000e01f0ser', remove_zwsp(u'u\U000e01f0ser'))

    def test_i18n_tag(self):

        def do_i18n_tag(string, *args):
            result = i18n_tag(string, *args)
            self.assertIsInstance(result, Fragment)
            return unicode(result).replace(u'<br/>', '<br />')

        self.assertEqual(
            do_i18n_tag('Try [1:downloading] the file instead',
                        tag.a(href='http://localhost/')),
            'Try <a href="http://localhost/">downloading</a> the file instead',
        )
        self.assertEqual(
            do_i18n_tag('[1:Note:] See [2:TracBrowser] for help ...',
                        tag.strong, tag.a(href='data:')),
            '<strong>Note:</strong> See <a href="data:">TracBrowser</a> for '
            'help ...',
        )
        self.assertEqual(
            do_i18n_tag('[1:Note:] See [2:TracBrowser] for help ...',
                        'strong', ('a', {'href': 'data:'})),
            '<strong>Note:</strong> See <a href="data:">TracBrowser</a> for '
            'help ...',
        )
        self.assertEqual(
            do_i18n_tag('Powered by [1:[2:Trac]][3:]By [4:Edgewall Software]',
                        tag.a(href='/about'), 'strong', 'br',
                        tag.a(href='https://www.edgewall.org/')),
            'Powered by <a href="/about"><strong>Trac</strong></a><br />By '
            '<a href="https://www.edgewall.org/">Edgewall Software</a>',
        )


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UtilTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
