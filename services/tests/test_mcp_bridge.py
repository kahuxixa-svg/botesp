import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('bridge', Path(__file__).parents[1] / 'mcp_bridge.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class BridgeTests(unittest.TestCase):
    def call(self, method, **params):
        return bridge.dispatch({'jsonrpc': '2.0', 'id': 4, 'method': method, 'params': params})

    def test_initialize_and_tool_inventory(self):
        self.assertEqual(self.call('initialize', protocolVersion='2024-11-05')['result']['protocolVersion'], '2024-11-05')
        self.assertEqual({t['name'] for t in self.call('tools/list')['result']['tools']},
                         {'troko_pc_status', 'troko_local_time'})

    def test_read_only_tools(self):
        value = self.call('tools/call', name='troko_pc_status', arguments={})['result']
        self.assertIn('memory_percent', json.loads(value['content'][0]['text']))
        value = self.call('tools/call', name='troko_local_time')['result']
        self.assertTrue(json.loads(value['content'][0]['text'])['datetime'].endswith('-05:00'))

    def test_rejects_unknown_tools_and_arguments(self):
        self.assertIn('error', self.call('tools/call', name='execute_shell', arguments={}))
        self.assertIn('error', self.call('tools/call', name='troko_pc_status', arguments={'path': 'private'}))

    def test_notifications_and_invalid_requests(self):
        self.assertIsNone(bridge.dispatch({'jsonrpc': '2.0', 'method': 'notifications/initialized'}))
        self.assertIn('error', bridge.dispatch([]))
        self.assertIn('error', self.call('not_a_method'))

    def test_normalizes_copied_url_without_forwarding_to_other_hosts(self):
        normalized = bridge.normalize_endpoint('wss\\://api.xiaozhi.me/mcp/?token=a.b.c&#x20;')
        self.assertEqual(normalized, 'wss://api.xiaozhi.me/mcp/?token=a.b.c')
        for value in ['ws://api.xiaozhi.me/mcp/?token=a.b.c',
                      'wss://example.com/mcp/?token=a.b.c',
                      'wss://api.xiaozhi.me/mcp/?token=a.b.c&token=d.e.f']:
            with self.assertRaises(ValueError): bridge.normalize_endpoint(value)


if __name__ == '__main__':
    unittest.main()
