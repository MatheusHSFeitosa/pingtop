import runpy
import subprocess
import unittest
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

APP = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'pingtop'))


def settings(**changes):
    config = dict(host='192.0.2.1', port='161', version='2c', community='community-test',
                  username='operator', level='noAuthNoPriv', auth='SHA',
                  auth_password='auth-test-password', privacy='AES',
                  privacy_password='privacy-test-password', oid='.1.3.6.1.2.1.1.1.0')
    config.update(changes)
    return config


class SnmpTest(unittest.TestCase):
    def test_transport_and_v3_security_levels(self):
        build = APP['snmp_command']
        command = build(settings(host='2001:db8::1', port='1161', version='3', level='authPriv'))
        self.assertEqual(command[-2:], ['udp6:[2001:db8::1]:1161', '.1.3.6.1.2.1.1.1.0'])
        for option in ('-u', '-l', '-a', '-A', '-x', '-X'):
            self.assertIn(option, command)
        command = build(settings(version='3'))
        self.assertNotIn('-A', command)
        self.assertNotIn('-X', command)
        self.assertNotIn('-c', command)

    def test_invalid_settings_fail_before_execution(self):
        for change in (dict(host='-host'), dict(port='65536'), dict(community=''),
                       dict(oid='invalid'), dict(version='3', level='authPriv', privacy_password='short')):
            with self.subTest(change=change), self.assertRaises(ValueError):
                APP['snmp_command'](settings(**change))

    def test_failures_and_secrets_in_returned_output(self):
        config = settings()
        with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess(
                [], 1, '', 'Error for community-test')):
            output = '\n'.join(APP['snmp_get'](config))
            self.assertIn('Consulta falhou', output)
            self.assertNotIn(config['community'], output)
        with patch.object(subprocess, 'run', side_effect=FileNotFoundError):
            self.assertIn('Instale o pacote snmp', APP['snmp_get'](config)[0])
        with patch.object(subprocess, 'run', side_effect=subprocess.TimeoutExpired([], 6)):
            self.assertIn('Tempo limite', APP['snmp_get'](config)[0])

    def test_bulk_and_walk_use_distinct_protocol_operations(self):
        bulk = APP['snmp_command'](settings(operation='BULK', repetitions='25', oid='.1'))
        self.assertEqual(bulk[0], 'snmpbulkget')
        self.assertIn('-Cn0', bulk)
        self.assertIn('-Cr25', bulk)
        walk = APP['snmp_command'](settings(operation='WALK', version='3', oid='.1'))
        self.assertEqual(walk[0], 'snmpwalk')
        self.assertNotIn('-Cr25', walk)
        self.assertEqual(walk[-1], '.1')
        with self.assertRaises(ValueError):
            APP['snmp_command'](settings(operation='BULK', repetitions='0'))

    def test_walk_preserves_partial_results_when_cancelled(self):
        cancel = threading.Event()
        cancel.set()
        process = MagicMock()
        process.communicate.return_value = (b'.1.3.6.1 = STRING: partial-result', None)
        process.returncode = -15
        context = MagicMock()
        context.__enter__.return_value = process
        with patch.object(subprocess, 'Popen', return_value=context):
            output = APP['snmp_get'](settings(operation='WALK'), cancel, [])
        process.terminate.assert_called_once()
        self.assertTrue(output[0].startswith('WALK cancelado'))
        self.assertIn('partial-result', output[1])

    def test_walk_streams_progress_then_collects_complete_output(self):
        process = MagicMock()
        process.communicate.side_effect = [
            subprocess.TimeoutExpired([], 0.2, output=b'.1.3.6.1 = STRING: first'),
            (b'.1.3.6.1 = STRING: first\n.1.3.6.2 = STRING: second', None),
        ]
        process.returncode = 0
        context = MagicMock()
        context.__enter__.return_value = process
        live = []
        with patch.object(subprocess, 'Popen', return_value=context):
            output = APP['snmp_get'](settings(operation='WALK'), threading.Event(), live)
        self.assertIn('first', live[0])
        self.assertTrue(output[0].startswith('WALK concluído'))
        self.assertIn('second', output[-1])
