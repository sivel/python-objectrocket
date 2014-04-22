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
Resource objects that represent ObjectRocket API resources
"""

from objectrocket import exceptions


class Resource(object):
    """Base resource class for specific resources"""
    __name__ = 'Resource'
    __identifier__ = 'name'

    def __init__(self, client, data):
        self.client = client
        self._data = data
        self._populate()

    def __repr__(self):
        return '<%s %s=%s>' % (self.__name__, self.__identifier__,
                               getattr(self, self.__identifier__))

    def _populate(self):
        """Populate self with attributes from the API response"""
        for k, v in list(self._data.items()):
            setattr(self, k, v)

    def get(self):
        """This method must be implemented by the specific resource"""
        raise exceptions.ObjectRocketNotImplementedError

    def delete(self):
        """This method must be implemented by the specific resource"""
        raise exceptions.ObjectRocketNotImplementedError

    def update(self):
        """This method must be implemented by the specific resource"""
        raise exceptions.ObjectRocketNotImplementedError

    def add(self):
        """This method must be implemented by the specific resource"""
        raise exceptions.ObjectRocketNotImplementedError

    def refresh(self):
        """This method must be implemented by the specific resource"""
        raise exceptions.ObjectRocketNotImplementedError


class Database(Resource):
    """Database resource class"""
    __name__ = 'Database'

    def refresh(self):
        """Refresh the details about the object, by pulling fro the API"""
        db = self.client.list_databases(name=self.name)
        self = db[0]

    def __getattr__(self, name):
        return self.get_collection(name)

    def get_collection(self, name):
        """Retrieve a collection from the API"""
        try:
            data = self.client.request('db/%s/collection/%s/stats/get' %
                                       (self.name, name))
        except exceptions.ObjectRocketNonZeroRC:
            data = dict()
        data.update({
            'name': name,
            'database': self
        })
        return Collection(self.client, data)


class Collection(Resource):
    """Collection resource class"""
    __name__ = 'Collection'

    def refresh(self):
        """Refresh the details about the object, by pulling fro the API"""
        self = self.database.get_collection(self.name)

    def add(self, doc=dict()):
        """Add a document to the collection"""
        return self.client.request('db/%s/collection/%s/add' %
                                   (self.database.name, self.name), doc=doc)

    def get(self, doc=dict()):
        """Retreive documents from the collection"""
        return self.client.request('db/%s/collection/%s/get' %
                                   (self.database.name, self.name), doc=doc)

    def update(self, doc=dict()):
        """Update documents in the collection"""
        return self.client.request('db/%s/collection/%s/update' %
                                   (self.database.name, self.name), doc=doc)

    def delete(self, doc=dict()):
        """Delete documents from the collection"""
        return self.client.request('db/%s/collection/%s/delete' %
                                   (self.database.name, self.name), doc=doc)


class ACL(Resource):
    """ACL resource class"""
    __name__ = 'ACL'
    __identifier__ = 'cidr_mask'

    def refresh(self):
        """Refresh the details about the object, by pulling fro the API"""
        acl = self.client.list_acls(name=self.name)
        self = acl[0]

    def delete(self):
        """Delete the ACL"""
        doc = {
            'cidr_mask': self.cidr_mask
        }
        self.client.request('acl/delete', doc=doc)
        return True
