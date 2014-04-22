python-objectrocket
===================

Python ObjectRocket API Client SDK

Usage
-----

.. code-block:: python

    import objectrocket.client
    client = objectrocket.client.Client('f8f0f3c679dd8b43e9ba934f4447e0cc')
    db = client.list_databases(name='test')[0]
    docs = db.test.get()
