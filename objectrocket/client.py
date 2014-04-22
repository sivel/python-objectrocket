# -*- coding: utf-8 -*-
# Copyright 2014 Matt Martz <matt@sivel.net>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Base client functions for communicating the the ObjectRocket API
"""

import json
import requests

from functools import wraps
from objectrocket import __version__

from objectrocket import exceptions
from objectrocket.resource import ACL, Database


def catch_http_exception(func):
    """Catch requests exceptions and raise ObjectRocketHTTPError exceptions"""
    @wraps(func)
    def _catch(*args, **kwargs):
        try:
            r = func(*args, **kwargs)
        except requests.RequestException as e:
            raise exceptions.ObjectRocketHTTPError(e)
        else:
            return r
    return _catch


class Client(object):
    """Base client class for communicating with the AP"""
    api_server = 'https://api.objectrocket.com'

    def __init__(self, api_key=None):
        self._session = None
        self._api_key = None
        self.api_key = api_key

    @property
    def api_key(self):
        """Getter for API key to ensure API key has been provided"""
        if self._api_key is None:
            raise exceptions.ObjectRocketNoApiKey('No API key provided')
        return self._api_key

    @api_key.setter
    def api_key(self, value):
        """Setter for API key to also create the requests session"""
        if value is not None:
            self._create_session()
        self._api_key = value

    @api_key.deleter
    def api_key(self):
        """Deleter for API key to remove the API key and destroy the session"""
        self._api_key = None
        self._session = None

    def _create_user_agent(self):
        """Build on the requests user-agent and add an ObjectRocket
        specifier

        """
        return '%s ObjectRocket/%s' % (requests.utils.default_user_agent(),
                                       __version__)

    def _create_session(self):
        """Create the requests session"""
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': self._create_user_agent(),
            'Accept': 'text/plain,application/json'
        })

    def _post_data(self, data={}):
        """Build out the post data to send with requests. The api_key must
        always exist in the post body, so this method helps us ensure
        that it is there

        """
        for k, v in list(data.items()):
            if not isinstance(v, str):
                data[k] = json.dumps(v)
        data.update({
            'api_key': self.api_key
        })
        return data

    def _parse_data(self, data):
        """Parse the JSON response data from the API, returning the 'data'
        attribute if the 'rc' value is 0, otherwise raise
        ObjectRocketNonZeroRC

        """
        if int(data['rc']) != 0:
            msg = data.get('msg', 'No msg provided (%s)' % data.get('data'))
            raise exceptions.ObjectRocketNonZeroRC(data['rc'], '%s' % msg)
        return data['data']

    @catch_http_exception
    def request(self, stub, doc={}, method='post'):
        """Helper method to perform the HTTP request and return the parsed
        API response data dictionary

        """
        url = '%s/%s' % (Client.api_server, stub.lstrip('/'))
        if doc is not None:
            post_data = self._post_data(dict(doc=doc))
        else:
            post_data = self._post_data()
        func = getattr(self._session, method.lower())
        r = func(url, data=post_data)
        r.raise_for_status()
        return self._parse_data(r.json())

    def get_details(self):
        """Retrieve details about the ObjectRocket instance"""
        return self.request('instance')

    def list_acls(self, cidr=None):
        """List all ACLs for the instance, optionally filtered by a cidr
        match

        """
        data = self.request('acl/get')
        acls = []
        for item in data:
            if cidr is None or cidr == item.get('cidr_mask'):
                acls.append(ACL(self, item))
        return acls

    def add_acl(self, cidr, description):
        """Add an ACL to the instance"""
        doc = {
            'cidr_mask': cidr,
            'description': description
        }
        self.request('acl/add', doc=doc)
        acl = self.list_acls(cidr=cidr)
        return acl[0]

    def delete_acl(self, cidr):
        """Delete an ACL fro the instance"""
        doc = {
            'cidr_mask': cidr
        }
        self.request('acl/delete', doc=doc)
        return True

    def list_databases(self, name=None):
        """List all datbases for this instance, optionally filtered by a
        name match

        """
        data = self.request('db')
        databases = []
        for item in data:
            if name is None or name == item.get('name'):
                databases.append(Database(self, item))
        return databases

    def add_database(self, name, user, password):
        """Add a database or database user. If the database does not exist
        it is created. If the database does exist only the user will be
        created

        """
        doc = {
            user: password
        }
        self.request('db/%s/add' % name, doc=doc)
        db = self.list_databases(name=name)
        return db[0]

    add_user = add_database

    def get_status(self, plus=False):
        """Get instance status details. Supply plus=True for extended
        status

        """
        stub = 'serverStatus%s' % ('Plus' if plus else '',)
        return self.request(stub)

    def get_space_usage(self):
        """Get space utilization for the instance"""
        return self.request('spaceusage/get')

    def get_logs(self):
        """Get logs for the instance"""
        return self.request('logs/get')

    def show_profile(self, doc={}):
        """Get profilter data from the instance"""
        return self.request('profiler/get', doc=doc)

    def get_profile_level(self):
        """Get the current profilter levels for all databases in the
        instance

        """
        return self.request('profiling_level/get')

    def set_profile_level(self, level=0, database=None, **kwargs):
        """Sets the profiling levels for one or more dbs in an instance"""
        if isinstance(database, Database):
            name = database.name
        else:
            name = database

        kwargs.update({'level': level})
        if name:
            kwargs.update({'db': name})

        return self.request('profiling_level/set', doc=kwargs)
