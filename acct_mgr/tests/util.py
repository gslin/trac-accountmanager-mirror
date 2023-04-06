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
from ..util import i18n_tag, pretty_precise_timedelta, remove_zwsp


class UtilTestCase(unittest.TestCase):

    def test_pretty_precise_timedelta(self):
        yesterday = datetime(2012, 12, 14)
        today = datetime(2012, 12, 15)
        tomorrow = datetime(2012, 12, 16)

        # Trac core compatible signature usage.
        self.assertEqual(pretty_precise_timedelta(None), '')
        self.assertEqual(pretty_precise_timedelta(None, None), '')
        self.assertEqual(pretty_precise_timedelta(today, today), '')
        self.assertEqual(pretty_precise_timedelta(today, tomorrow), '1 day')
        self.assertEqual(pretty_precise_timedelta(today, yesterday), '1 day')
        self.assertEqual(pretty_precise_timedelta(tomorrow, yesterday),
                         '2 days')

        # Alternative `diff` keyword argument usage.
        self.assertEqual(pretty_precise_timedelta(None, diff=0), '')
        # Use ngettext with default locale (English).
        self.assertEqual(pretty_precise_timedelta(None, diff=1), '1 second')
        self.assertEqual(pretty_precise_timedelta(None, diff=2), '2 seconds')
        # Limit resolution.
        self.assertEqual(pretty_precise_timedelta(None, diff=3, resolution=4),
                         'less than 4 seconds')
        self.assertEqual(pretty_precise_timedelta(None, diff=86399),
                         '23:59:59')
        self.assertEqual(pretty_precise_timedelta(None, diff=86400),
                         '1 day')
        self.assertEqual(pretty_precise_timedelta(None, diff=86401),
                         '1 day 1 second')

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
