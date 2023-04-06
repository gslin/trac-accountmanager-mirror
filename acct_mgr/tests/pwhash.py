# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Jun Omae <jun66j5@gmail.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest

try:
    import bcrypt
except ImportError:
    bcrypt = None

from ..pwhash import (
    passlib, crypt, generate_hash, check_hash, _passlib_generate_hash,
    _passlib_check_hash, _crypt_generate_hash, _crypt_check_hash,
    _unavai_generate_hash, _unavai_check_hash,
)


_PASSWORD = 'wesViWip.Actyur3'
_HASHES = {
    'crypt': 'dZn8UE10rIAR6',
    'md5': '$apr1$975LB2J8$pbifv0nfpzcxQ9gSe2tdM0',
    'sha': '{SHA}91NeIA99KkOtqtRlpl4Z8jC4hlA=',
    'sha256': '$5$rounds=2500$cZbJvPaLtPHPcPsa$5YC2vX.WXMmsXEinQuG50P48CLeZddf'
              'YUPr7dczt2n5',
    'sha512': '$6$rounds=2500$6yz3SzAbZhCb5Whm$aggkw/9XqtO4dhrlyXAhI7M/8o3vTBk'
              'XrZ071QikKDnOtUv6DkafqbPtfAr8nuOfgoB1dXPwwxpcgAJc01x/P0',
    'bcrypt': '$2b$11$oshDukXxHZQvPEOBonYqDehZ0QXnpqkc2jamNS/35vlfZ41psDL4O',
}


class BaseTestCase(unittest.TestCase):

    methods = ()
    generate_hash = None
    check_hash = None

    def _test_prefix(self, method, prefix):
        if method not in self.methods:
            raise unittest.SkipTest('%s unsupported' % method)
        hash_ = self.generate_hash(_PASSWORD, method)
        self.assertTrue(hash_.startswith(prefix),
                        "%r doesn't start with %r" % (hash_, prefix))

    def test_md5_prefix(self):
        self._test_prefix('md5', '$apr1$')

    def test_sha_prefix(self):
        self._test_prefix('sha', '{SHA}')

    def test_sha256_prefix(self):
        self._test_prefix('sha256', '$5$')

    def test_sha512_prefix(self):
        self._test_prefix('sha512', '$6$')

    def test_bcrypt_prefix(self):
        self._test_prefix('bcrypt', ('$2b$', '$2a$'))

    def test_generate_hash(self):
        for method in self.methods:
            hash1 = self.generate_hash(_PASSWORD, method)
            hash2 = self.generate_hash(_PASSWORD, method)
            if method == 'sha':
                self.assertTrue(self.check_hash(_PASSWORD, hash1))
                self.assertEqual(hash1, hash2)
            else:
                self.assertTrue(self.check_hash(_PASSWORD, hash1))
                self.assertTrue(self.check_hash(_PASSWORD, hash2))
                self.assertNotEqual(hash1, hash2)

    def test_check_hash(self):
        for method in self.methods:
            hash_ = _HASHES[method]
            self.assertTrue(self.check_hash(_PASSWORD, hash_))


def _passlib_methods():
    if not passlib:
        return ()
    methods = ['crypt', 'md5', 'sha', 'sha256', 'sha512']
    if bcrypt:
        methods.append('bcrypt')
    return frozenset(methods)


def _crypt_metdhos():
    if not crypt:
        return ()
    methods = ['md5', 'sha']
    if hasattr(crypt, 'methods'):
        pairs = [
            ('crypt', 'METHOD_CRYPT'),
            ('sha256', 'METHOD_SHA256'),
            ('sha512', 'METHOD_SHA512'),
            ('bcrypt', 'METHOD_BLOWFISH'),
        ]
        for name, method in pairs:
            if getattr(crypt, method, None) in crypt.methods:
                methods.append(name)
    return frozenset(methods)


@unittest.skipUnless(passlib, 'passlib unavailable')
class PasslibTestCase(BaseTestCase):

    methods = _passlib_methods()

    def generate_hash(self, password, method):
        return _passlib_generate_hash(password, method)

    def check_hash(self, password, hash):
        return _passlib_check_hash(password, hash)


@unittest.skipUnless(crypt, 'crypt unavailable')
class CryptTestCase(BaseTestCase):

    methods = _crypt_metdhos()

    def generate_hash(self, password, method):
        return _crypt_generate_hash(password, method)

    def check_hash(self, password, hash):
        return _crypt_check_hash(password, hash)
class MethodTestCase(unittest.TestCase):

    def test_methods(self):
        if passlib:
            self.assertEqual(generate_hash, _passlib_generate_hash)
            self.assertEqual(check_hash, _passlib_check_hash)
        elif crypt:
            self.assertEqual(generate_hash, _crypt_generate_hash)
            self.assertEqual(check_hash, _crypt_check_hash)
        else:
            self.assertEqual(generate_hash, _unavai_generate_hash)
            self.assertEqual(check_hash, _unavai_check_hash)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PasslibTestCase))
    suite.addTest(unittest.makeSuite(CryptTestCase))
    suite.addTest(unittest.makeSuite(MethodTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
