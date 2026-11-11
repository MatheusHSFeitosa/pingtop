import runpy
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

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
