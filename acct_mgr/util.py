# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
# Copyright (C) 2010-2013 Steffen Hoffmann <hoff.st@web.de>
# Copyright (C) 2011 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Matthew Good <trac@matt-good.net>

import os
import re

try:
    from babel.support import LazyProxy
except ImportError:
    LazyProxy = None

from trac.config import Option
from trac.util.datefmt import format_datetime, to_datetime, utc
from trac.util.html import tag

from .api import _, ngettext
from .compat import basestring


class EnvRelativePathOption(Option):
    def __get__(self, instance, owner):
        if instance is None:
            return self
        path = super(EnvRelativePathOption, self).__get__(instance, owner)
        if not path:
            return path
        return os.path.normpath(os.path.join(instance.env.path, path))


# taken from a comment of Horst Hansen
# at http://code.activestate.com/recipes/65441
def contains_any(str, set):
    for c in set:
        if c in str:
            return True
    return False


def if_enabled(func):
    def wrap(self, *args, **kwds):
        if not self.enabled:
            return None
        return func(self, *args, **kwds)

    return wrap


def pretty_precise_timedelta(time1, time2=None, resolution=None, diff=0):
    """Calculate time delta between two `datetime` objects and format
    for pretty-printing.

    If either `time1` or `time2` is None, the current time will be used
    instead.  Extending the signature of trac.util.datefmt.pretty_timedelta
    pre-calculated timedeltas may be specified by the alternative `diff`
    keyword argument that takes precedence if used.
    """
    if diff:
        age_s = diff
    else:
        time1 = to_datetime(time1)
        time2 = to_datetime(time2)
        if time1 > time2:
            time2, time1 = time1, time2
        diff = time2 - time1
        age_s = int(diff.days * 86400 + diff.seconds)
    age_d = age_s // 86400

    # DEVEL: Always reduce resolution as required by `resolution` argument.
    if resolution:
        if age_s < resolution:
            delta = pretty_precise_timedelta(None, diff=resolution)
            return _("less than %s") % delta
    # Get a compact string by stripping non-significant parts.
    if age_s == 0:
        return ''
    # Show seconds for small time values, even in timedeltas > 1 day.
    t = age_s - age_d * 86400
    if 0 < t < 120:
        t = ngettext('%(num)i second', '%(num)i seconds', t)
        if age_d == 0:
            return t
    elif age_d != age_s / 86400.0:
        t = format_datetime(age_s - age_d * 86400, format='%X', tzinfo=utc)
        if age_d == 0:
            return t
    # TRANSLATOR: Pretty datetime representation, time part provided by
    # string substitution.
    return (ngettext("%(num)i day %%s", "%(num)i days %%s", age_d)
            % (str(t) != '0' and t or '')).rstrip()


def _create_zwsp_re():
    ucs2_range = u'\\s\u200b-\u200f\u061c\u202a-\u202e\u2066-\u2069\u00ad' \
                 u'\u2060\ufeff\u2061-\u2064\u115f\u1160\u180b-\u180d' \
                 u'\ufe00-\ufe0f'
    try:
        pattern = re.compile(u'[%s\U000e0100-\U000e01ef]+' % ucs2_range,
                             re.UNICODE)
    except re.error:
        # Narrow build, `re` cannot use characters >= 0x10000
        pattern = re.compile(u'[%s]+|(?:\udb40[\udd00-\uddef])+' % ucs2_range,
                             re.UNICODE)
    return pattern


_zwsp_re = _create_zwsp_re()


def remove_zwsp(text):
    """Strips unicode zero-width and whitespace characters.
    """
    return _zwsp_re.sub('', text)


_i18n_tag_re = re.compile(r'(?:\[([1-9][0-9]*)\:)|(?<!\\)\]')


def i18n_tag(string, *args, **kwargs):
    START = 'start'
    END = 'end'
    TEXT = 'text'

    def parse(string):
        stack = [0]
        while True:
            mo = _i18n_tag_re.search(string)
            if not mo:
                break

            if mo.start() or stack[-1]:
                yield TEXT, stack[-1], string[:mo.start()]
            string = string[mo.end():]

            orderno = mo.group(1)
            if orderno is not None:
                orderno = int(orderno)
                stack.append(orderno)
                yield START, orderno, None
            else:
                yield END, stack.pop(), None
            if not stack:
                break

        if string:
            yield TEXT, stack[-1], string

    def to_element(arg):
        if isinstance(arg, (tuple, list)):
            arg = tag.__getattr__(arg[0])(**arg[1])
        elif isinstance(arg, basestring):
            arg = tag.__getattr__(arg)
        return arg

    def generate(string, args, kwargs):
        fragment = tag()
        args = (fragment,) + tuple(to_element(arg) for arg in args)
        stack = [fragment]
        for kind, n, data in parse(string):
            if kind is TEXT:
                if data:
                    stack[-1].append(data % kwargs if kwargs else data)
                continue
            if kind is START:
                if 0 <= n < len(args):
                    arg = args[n]
                else:
                    raise IndexError('index %d out of range (%d given for %r)'
                                     % (n, len(args), string))
                stack[-1].append(arg)
                stack.append(arg)
                continue
            if kind is END:
                stack.pop()
                continue
        return fragment

    if LazyProxy and isinstance(string, LazyProxy):
        string = string.value
    return generate(string, args, kwargs)
