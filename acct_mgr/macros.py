# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Steffen Hoffmann <hoff.st@web.de>

from trac.core import Component, implements
from trac.perm import PermissionSystem
from trac.util.html import html as tag
from trac.web.chrome import Chrome
from trac.wiki.api import IWikiMacroProvider, WikiSystem, parse_args
from trac.wiki.formatter import format_to_oneliner

from .admin import fetch_user_data
from .api import AccountManager, tag_
from .guard import AccountGuard


class AccountManagerWikiMacros(Component):
    """Provides wiki macros related to Trac accounts/authenticated users."""

    implements(IWikiMacroProvider)

    # IWikiMacroProvider

    def get_macros(self):
        yield 'ProjectStats'
        yield 'UserQuery'

    def get_macro_description(self, name):
        if name == 'ProjectStats':
            return """Wiki macro listing some generic Trac statistics.

This macro accepts a comma-separated list of keyed parameters, in the form
"key=value". Valid keys:
 * '''wiki''' -- statistics for TracWiki, values:
  * ''count'' -- show wiki page count
 * '''prefix''' -- use with ''wiki'' key: only names that start with that
 prefix are included

'count' is also recognized without prepended key name.
"""

        elif name == 'UserQuery':
            return """Wiki macro listing users that match certain criteria.

This macro accepts a comma-separated list of keyed parameters, in the form
"key=value". Valid keys:
 * '''perm''' -- show only that users, a permission action given by ''value''
 has been granted to
 * '''locked''' -- retrieve users, who's account has/has not been locked
 depending on boolean value
 * '''format''' -- output style: 'count', 'list' or comma-separated values
 (default)
 * '''nomatch''' -- replacement wiki markup that is displayed, if there's
 no match and output style isn't 'count' either

'count' is also recognized without prepended key name. Other non-keyed
parameters are:
 * '''locked''' -- alias for 'locked=True'
 * '''visit''' -- show a list of accounts with last-login information, only
 available in table format
 * '''name''' -- forces replacement of matching username with their
 corresponding full names, if available; adds a full names column if combined
 with 'visit'
 * '''email''' -- append email address to usernames, if available

Requires `USER_VIEW` permission for output in any format other then 'count'.
A misc placeholder with this statement is presented to unprivileged users.
"""

    def expand_macro(self, formatter, name, content):
        env = formatter.env
        req = formatter.req
        if not content:
            args = []
            kw = {}
        else:
            args, kw = parse_args(content)
        if name == 'ProjectStats':
            if 'wiki' in kw:
                prefix = 'prefix' in kw and kw['prefix'] or None
                wiki = WikiSystem(env)
                if kw['wiki'] == 'count' or 'count' in args:
                    return tag(len(list(wiki.get_pages(prefix))))
        elif name == 'UserQuery':
            msg_no_perm = tag.p(tag_("(required %(perm)s missing)",
                                     perm=tag.strong('USER_VIEW')),
                                class_='hint')
            if 'perm' in kw:
                perm_sys = PermissionSystem(self.env)
                users = perm_sys.get_users_with_permission(kw['perm'].upper())
            else:
                acct_mgr = AccountManager(env)
                users = list(set(acct_mgr.get_users()))
            if 'locked' in kw or 'locked' in args:
                guard = AccountGuard(env)
                locked = []
                for user in users:
                    if guard.user_locked(user):
                        locked.append(user)
                if kw.get('locked', 'True').lower() in ('true', 'yes', '1'):
                    users = locked
                else:
                    users = list(set(users) - set(locked))
            elif 'visit' in kw or 'visit' in args:
                if 'USER_VIEW' not in req.perm:
                    return msg_no_perm
                cols = []
                data = {'accounts': fetch_user_data(env, req), 'cls': 'wiki'}
                for col in ('email', 'name'):
                    if col in args:
                        cols.append(col)
                data['cols'] = cols
                return Chrome(env).render_template(
                    req, 'account_user_table.html', data, 'text/html', True)
            if kw.get('format') == 'count' or 'count' in args:
                return tag(len(users))
            if 'USER_VIEW' not in req.perm:
                return msg_no_perm
            if 'email' in args or 'name' in args:
                # Replace username with full name, add email if available.
                for username, name, email in self.env.get_known_users():
                    if username in users:
                        if 'name' not in args or name is None:
                            name = username
                        if 'email' in args and email is not None:
                            email = ''.join(['<', email, '>'])
                            name = ' '.join([name, email])
                        if not username == name:
                            users.pop(users.index(username))
                            users.append(name)
            if not users and 'nomatch' in kw:
                return format_to_oneliner(env, formatter.context,
                                          kw['nomatch'])
            users = sorted(users)
            if kw.get('format') == 'list':
                return tag.ul([tag.li(Chrome(env).format_author(req, user))
                               for user in users])
            else:
                # Default output format: comma-separated list.
                return tag(', '.join([Chrome(env).format_author(req, user)
                                      for user in users]))
