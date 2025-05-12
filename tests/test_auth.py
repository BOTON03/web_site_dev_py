# tests/test_auth.py
import unittest
from zoho_sync.zoho.auth import get_access_token

class TestAuth(unittest.TestCase):
    def test_get_access_token(self):
        token = get_access_token()
        self.assertIsNotNone(token)
