# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Matthew Good <trac@matt-good.net>
# Copyright (C) 2011 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Matthew Good <trac@matt-good.net>

import base64
import hashlib

try:
    import passlib
except ImportError:
    passlib = None

try:
    import crypt
except ImportError:
    crypt = None

from trac.config import Option
from trac.core import Component, Interface, implements

from .api import _, N_
from .compat import compare_digest, unicode


class IPasswordHashMethod(Interface):

    def generate_hash(user, password):
        pass

    def check_hash(user, password, hash):
        pass


class HtPasswdHashMethod(Component):
    implements(IPasswordHashMethod)

    hash_type = Option('account-manager', 'db_htpasswd_hash_type', 'crypt',
        doc="Default hash type of new/updated passwords")

    def generate_hash(self, user, password):
        return generate_hash(password, self.hash_type)

    def check_hash(self, user, password, hash):
        return check_hash(password, hash)


class HtDigestHashMethod(Component):

    implements(IPasswordHashMethod)

    realm = Option('account-manager', 'db_htdigest_realm', '',
        doc=N_("Realm to select relevant htdigest db entries"))

    def generate_hash(self, user, password):
        hash_ = htdigest(user, self.realm, password)
        return '%s:%s' % (self.realm, hash_)

    def check_hash(self, user, password, hash):
        return compare_digest(hash, self.generate_hash(user, password))


def htdigest(user, realm, password):
    p = ':'.join([user, realm, password]).encode('utf-8')
    return hashlib.md5(p).hexdigest()


if passlib:
    from passlib.context import CryptContext
    from passlib.hash import bcrypt
    from .compat import itervalues

    _passlib_schemes = {
        'sha256': 'sha256_crypt',
        'sha512': 'sha512_crypt',
        'md5': 'apr_md5_crypt',
        'crypt': 'des_crypt',
    }
    try:
        bcrypt.get_backend()
    except passlib.exc.MissingBackendError:
        pass
    else:
        _passlib_schemes['bcrypt'] = 'bcrypt'
    _passlib_context = CryptContext(schemes=list(itervalues(_passlib_schemes)))

    if not hasattr(_passlib_context, 'handler'):
        # passlib 1.5 and early
        def _passlib_hash(password, scheme):
            return _passlib_context.encrypt(password, scheme=scheme)
    elif hasattr(_passlib_context.handler('sha512_crypt'), 'hash'):
        # passlib 1.7+
        def _passlib_hash(password, scheme):
            handler = _passlib_context.handler(scheme)
            return handler.hash(password)
    else:
        # passlib 1.6
        def _passlib_hash(password, scheme):
            handler = _passlib_context.handler(scheme)
            return handler.encrypt(password)

    def _passlib_generate_hash(password, method):
        if method == 'sha':
            return _sha_digest(password)
        if method not in _passlib_schemes:
            method = 'crypt'
        scheme = _passlib_schemes[method]
        return _passlib_hash(password, scheme)

    def _passlib_check_hash(password, the_hash):
        if the_hash.startswith('{SHA}'):
            return compare_digest(the_hash, _sha_digest(password))
        try:
            return _passlib_context.verify(password, the_hash)
        except ValueError:
            return False

else:
    _passlib_generate_hash = _passlib_check_hash = None


if not crypt:
    _crypt_generate_hash = _crypt_check_hash = None

elif hasattr(crypt, 'methods'):  # Python 3
    from trac.util import salt, md5crypt

    def _crypt_methods():
        pairs = [
            ('crypt', 'METHOD_CRYPT'),
            ('sha256', 'METHOD_SHA256'),
            ('sha512', 'METHOD_SHA512'),
            ('bcrypt', 'METHOD_BLOWFISH'),
        ]
        pairs = [(name, getattr(crypt, method, None)) for name, method
                                                      in pairs]
        return dict((name, method) for name, method in pairs if method)

    _crypt_methods = _crypt_methods()

    def _crypt_generate_hash(password, method):
        if method == 'md5':
            return md5crypt(password, salt(), '$apr1$')
        if method == 'sha':
            return _sha_digest(password)
        if method not in _crypt_methods:
            method = 'crypt'
        return crypt.crypt(password, crypt.mksalt(_crypt_methods[method]))

    def _crypt_check_hash(password, the_hash):
        if the_hash.startswith('$apr1$'):
            salt = the_hash[6:].split('$', 1)[0]
            hash_ = md5crypt(password, salt, '$apr1$')
        elif the_hash.startswith('{SHA}'):
            hash_ = _sha_digest(password)
        else:
            hash_ = crypt.crypt(password, the_hash)
        return compare_digest(hash_, the_hash)

else:  # Python 2
    from trac.util import salt, md5crypt

    def _crypt_generate_hash(password, method):
        password = password.encode('utf-8') \
                   if isinstance(password, unicode) else password
        if method == 'md5':
            return md5crypt(password, salt(2), '$apr1$')
        if method == 'sha':
            return _sha_digest(password)
        return crypt.crypt(password, salt(2))

    def _crypt_check_hash(password, the_hash):
        password = password.encode('utf-8') \
                   if isinstance(password, unicode) else password
        if the_hash.startswith('$apr1$'):
            salt = the_hash[6:].split('$', 1)[0]
            hash_ = md5crypt(password, salt, '$apr1$')
        elif the_hash.startswith('{SHA}'):
            hash_ = _sha_digest(password)
        else:
            hash_ = crypt.crypt(password, the_hash)
        return compare_digest(hash_, the_hash)


def _sha_digest(password):
    digest = hashlib.sha1(password.encode('utf-8')).digest()
    return u'{SHA}' + unicode(base64.b64encode(digest), 'ascii')


def _unavai_error():
    return NotImplementedError(_("Neither passlib nor crypt module available"))

def _unavai_generate_hash(password, method):
    raise _unavai_error()

def _unavai_check_hash(password, the_hash):
    raise _unavai_error()


if passlib:
    generate_hash = _passlib_generate_hash
    check_hash = _passlib_check_hash

elif crypt:
    generate_hash = _crypt_generate_hash
    check_hash = _crypt_check_hash

else:
    generate_hash = _unavai_generate_hash
    check_hash = _unavai_check_hash
