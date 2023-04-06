# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Matthew Good <trac@matt-good.net>
# Copyright (C) 2010-2014 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import hmac
import sys

from trac.web.chrome import Chrome


if sys.version_info[0] == 2:
    unicode = unicode
    basestring = basestring
    iteritems = lambda d: d.iteritems()
    itervalues = lambda d: d.itervalues()

    def compare_digest(a, b):
        if type(a) is not type(b):
            to_b = lambda v: v.encode('utf-8') if isinstance(v, unicode) else v
            a = to_b(a)
            b = to_b(b)
        return hmac.compare_digest(a, b)

else:
    unicode = str
    basestring = str
    iteritems = lambda d: d.items()
    itervalues = lambda d: d.values()
    compare_digest = hmac.compare_digest

use_jinja2 = hasattr(Chrome, 'jenv')

if use_jinja2:
    def process_request_compat(f):
        return f
else:
    def process_request_compat(f):
        def wrapper(self, req):
            rv = f(self, req)
            if isinstance(rv, tuple) and len(rv) == 2:
                rv += (None,)
            return rv
        return wrapper
