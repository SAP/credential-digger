import os
import tempfile
import unittest

import pandas as pd

from credentialdigger.cli import cli
from credentialdigger.client_sqlite import SqliteClient
from parameterized import param, parameterize

class TestGetDiscoveries(unittest.TestCase):
    pass