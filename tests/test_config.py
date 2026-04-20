import unittest
import sys
import importlib
from unittest.mock import MagicMock

# Mock external dependencies before importing config
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Delete mocked config from other tests if present
if 'config' in sys.modules and isinstance(sys.modules['config'], MagicMock):
    del sys.modules['config']

import config
# Force reload to ensure we have the real module
importlib.reload(config)

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Save original values
        self.original_dry_run = config.DRY_RUN
        self.original_private_key = config.PRIVATE_KEY
        self.original_wallet_address = config.WALLET_ADDRESS

    def tearDown(self):
        # Restore original values
        config.DRY_RUN = self.original_dry_run
        config.PRIVATE_KEY = self.original_private_key
        config.WALLET_ADDRESS = self.original_wallet_address

    def test_validate_dry_run_true(self):
        config.DRY_RUN = True
        config.PRIVATE_KEY = ""
        config.WALLET_ADDRESS = ""
        # Should not raise exception
        try:
            config.validate()
        except Exception as e:
            self.fail(f"validate() raised {e} unexpectedly!")

    def test_validate_dry_run_false_missing_creds(self):
        config.DRY_RUN = False
        config.PRIVATE_KEY = ""
        config.WALLET_ADDRESS = ""
        with self.assertRaises(EnvironmentError) as context:
            config.validate()
        self.assertEqual(str(context.exception), "Mancano credenziali nel .env")

    def test_validate_dry_run_false_with_creds(self):
        config.DRY_RUN = False
        config.PRIVATE_KEY = "0x123"
        config.WALLET_ADDRESS = "0x456"
        # Should not raise exception
        try:
            config.validate()
        except Exception as e:
            self.fail(f"validate() raised {e} unexpectedly!")

if __name__ == '__main__':
    unittest.main()
