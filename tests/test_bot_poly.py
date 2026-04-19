import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import os
import sys

# Mock modules before importing bot_poly
sys.modules['modules.poly_watcher'] = MagicMock()
sys.modules['modules.price_feed'] = MagicMock()
sys.modules['poly_trader'] = MagicMock()
sys.modules['config'] = MagicMock()
sys.modules['modules.logger'] = MagicMock()
sys.modules['requests'] = MagicMock()

# Import the functions to test
from bot_poly import load_trades_log, save_trade, TRADES_LOG

class TestBotPoly(unittest.TestCase):

    @patch('os.path.exists')
    def test_load_trades_log_not_exists(self, mock_exists):
        mock_exists.return_value = False
        result = load_trades_log()
        self.assertEqual(result, [])
        mock_exists.assert_called_once_with(TRADES_LOG)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='[{"id": 1}]')
    def test_load_trades_log_exists(self, mock_file, mock_exists):
        mock_exists.return_value = True
        result = load_trades_log()
        self.assertEqual(result, [{"id": 1}])
        mock_exists.assert_called_once_with(TRADES_LOG)
        mock_file.assert_called_once_with(TRADES_LOG)

    @patch('bot_poly.load_trades_log')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_trade(self, mock_json_dump, mock_file, mock_load):
        mock_load.return_value = [{"id": 1}]
        new_entry = {"id": 2}

        save_trade(new_entry)

        mock_load.assert_called_once()
        mock_file.assert_called_once_with(TRADES_LOG, "w")

        # Verify json.dump was called with the combined list
        args, _ = mock_json_dump.call_args
        self.assertEqual(args[0], [{"id": 1}, {"id": 2}])

if __name__ == '__main__':
    unittest.main()
