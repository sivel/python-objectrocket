import unittest
import objectrocket

from distutils.version import StrictVersion

class TestInit(unittest.TestCase):
    def test_version(self):
        StrictVersion(objectrocket.__version__)
