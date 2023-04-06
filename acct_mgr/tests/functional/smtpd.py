# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Matthew Good <trac@matt-good.net>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Author: Pedro Algarvio <ufs@ufsoft.org>

from __future__ import absolute_import

import asyncore
import smtpd
import threading


class NonForgetingSMTPServerStore(object):
    """
    Non forgetting store for SMTP data.
    """
    # We override trac's implementation of a mailstore because if forgets
    # the last message when a new one arrives.
    # Account Manager at times sends more than one email and we need to be
    # able to test both

    def __init__(self):
        self.messages = {}
        self.last_message = {}

    @property
    def recipients(self):
        return self.last_message.get('recipients')

    @property
    def sender(self):
        return self.last_message.get('sender')

    @property
    def message(self):
        return self.last_message.get('message')

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        message = {'recipients': rcpttos, 'sender': mailfrom, 'message': data}
        self.messages.update((recipient, message) for recipient in rcpttos)
        self.last_message = message

    def full_reset(self):
        self.messages.clear()
        self.last_message.clear()


class SMTPServer(smtpd.SMTPServer):

    store = None

    def __init__(self, localaddr, store):
        smtpd.SMTPServer.__init__(self, localaddr, None)
        self.store = store

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        self.store.process_message(peer, mailfrom, rcpttos, data, **kwargs)


class SMTPThreadedServer(threading.Thread):
    """
    Run a SMTP server for a single connection, within a dedicated thread
    """
    host = 'localhost'

    def __init__(self, port):
        self.port = port
        self.store = NonForgetingSMTPServerStore()
        super(SMTPThreadedServer, self).__init__(target=asyncore.loop,
                                                 args=(0.1, True))
        self.daemon = True

    def start(self):
        self.server = SMTPServer((self.host, self.port), self.store)
        super(SMTPThreadedServer, self).start()

    def stop(self):
        self.server.close()
        self.join()

    def get_sender(self, recipient=None):
        """Return the sender of a message. If recipient is passed, return
        the sender for the message sent to that recipient, else, send
        the sender for last message"""
        try:
            return self.store.messages[recipient]['sender']
        except KeyError:
            return self.store.sender

    def get_recipients(self, recipient=None):
        """Return the recipients of a message. If recipient is passed, return
        the recipients for the message sent to that recipient, else, send
        recipients for last message"""
        try:
            return self.store.messages[recipient]['recipients']
        except KeyError:
            return self.store.recipients

    def get_message(self, recipient=None):
        """Return the message of a message. If recipient is passed, return
        the actual message for the message sent to that recipient, else, send
        the last message"""
        try:
            return self.store.messages[recipient]['message']
        except KeyError:
            return self.store.message

    def get_message_parts(self, recipient):
        """Return the message parts(dict). If recipient is passed, return
        the parts for the message sent to that recipient, else, send the parts
        for last message"""
        try:
            return self.store.messages[recipient]
        except KeyError:
            return None

    def full_reset(self):
        self.store.full_reset()
