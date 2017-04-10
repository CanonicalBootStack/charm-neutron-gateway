import collections

from mock import MagicMock, call, patch, ANY

import charmhelpers.core.hookenv as hookenv
import neutron_utils
try:
    import neutronclient
except ImportError:
    neutronclient = None

from test_utils import (
    CharmTestCase
)

TO_PATCH = [
    'config',
    'get_os_codename_install_source',
    'apt_update',
    'apt_upgrade',
    'apt_install',
    'configure_installation_source',
    'git_src_dir',
    'log',
    'add_bridge',
    'add_bridge_port',
    'headers_package',
    'full_restart',
    'os_release',
    'service',
    'service_running',
    'NetworkServiceContext',
    'ExternalPortContext',
    'unit_private_ip',
    'relations_of_type',
    'render',
    'service_stop',
    'determine_dkms_package',
    'service_restart',
    'is_relation_made',
    'lsb_release',
    'mkdir',
    'copy2',
    'init_is_systemd',
    'os_application_version_set',
    'NeutronAPIContext',
]

openstack_origin_git = \
    """repositories:
         - {name: requirements,
            repository: 'git://git.openstack.org/openstack/requirements',
            branch: stable/juno}
         - {name: neutron,
            repository: 'git://git.openstack.org/openstack/neutron',
            branch: stable/juno}"""


class TestNeutronUtils(CharmTestCase):

    def assertDictEqual(self, d1, d2, msg=None):  # assertEqual uses for dicts
        for k, v1 in d1.iteritems():
            self.assertIn(k, d2, msg)
            v2 = d2[k]
            if(isinstance(v1, collections.Iterable) and
               not isinstance(v1, basestring)):
                self.assertItemsEqual(v1, v2, msg)
            else:
                self.assertEqual(v1, v2, msg)

    def setUp(self):
        super(TestNeutronUtils, self).setUp(neutron_utils, TO_PATCH)
        self.headers_package.return_value = 'linux-headers-2.6.18'
        self._set_distrib_codename('trusty')

    def tearDown(self):
        # Reset cached cache
        hookenv.cache = {}

    def _set_distrib_codename(self, newcodename):
        self.lsb_release.return_value = {'DISTRIB_CODENAME': newcodename}

    def test_valid_plugin(self):
        self.config.return_value = 'ovs'
        self.assertTrue(neutron_utils.valid_plugin())
        self.config.return_value = 'nsx'
        self.assertTrue(neutron_utils.valid_plugin())

    def test_invalid_plugin(self):
        self.config.return_value = 'invalid'
        self.assertFalse(neutron_utils.valid_plugin())

    def test_get_early_packages_ovs(self):
        self.config.return_value = 'ovs'
        self.determine_dkms_package.return_value = [
            'openvswitch-datapath-dkms']
        self.assertEquals(
            neutron_utils.get_early_packages(),
            ['openvswitch-datapath-dkms', 'linux-headers-2.6.18'])

    def test_get_early_packages_nsx(self):
        self.config.return_value = 'nsx'
        self.assertEquals(
            neutron_utils.get_early_packages(),
            [])

    def test_get_early_packages_empty(self):
        self.config.return_value = 'noop'
        self.assertEquals(neutron_utils.get_early_packages(),
                          [])

    @patch.object(neutron_utils, 'git_install_requested')
    def test_get_packages_ovs_icehouse(self, git_requested):
        git_requested.return_value = False
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'icehouse'
        self.assertTrue('neutron-vpn-agent' in neutron_utils.get_packages())
        self.assertFalse('neutron-l3-agent' in neutron_utils.get_packages())

    @patch.object(neutron_utils, 'git_install_requested')
    def test_get_packages_ovs_juno_utopic(self, git_requested):
        git_requested.return_value = False
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'juno'
        self._set_distrib_codename('utopic')
        self.assertFalse('neutron-vpn-agent' in neutron_utils.get_packages())
        self.assertTrue('neutron-l3-agent' in neutron_utils.get_packages())

    @patch.object(neutron_utils, 'git_install_requested')
    def test_get_packages_ovs_juno_trusty(self, git_requested):
        git_requested.return_value = False
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'juno'
        self.assertTrue('neutron-vpn-agent' in neutron_utils.get_packages())
        self.assertFalse('neutron-l3-agent' in neutron_utils.get_packages())

    @patch.object(neutron_utils, 'git_install_requested')
    def test_get_packages_ovs_kilo(self, git_requested):
        git_requested.return_value = False
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'kilo'
        self.assertTrue('python-neutron-fwaas' in neutron_utils.get_packages())

    @patch.object(neutron_utils, 'git_install_requested')
    def test_get_packages_ovs_liberty(self, git_requested):
        git_requested.return_value = False
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'liberty'
        packages = neutron_utils.get_packages()
        self.assertTrue('neutron-metering-agent' in packages)
        self.assertFalse('neutron-plugin-metering-agent' in packages)
        self.assertFalse('python-mysqldb' in packages)
        self.assertTrue('python-pymysql' in packages)

    @patch.object(neutron_utils, 'git_install_requested')
    def test_get_packages_ovs_mitaka(self, git_requested):
        git_requested.return_value = False
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'mitaka'
        packages = neutron_utils.get_packages()
        self.assertTrue('neutron-metering-agent' in packages)
        self.assertFalse('neutron-plugin-metering-agent' in packages)
        self.assertTrue('neutron-openvswitch-agent' in packages)
        self.assertFalse('neutron-plugin-openvswitch-agent' in packages)
        self.assertFalse('python-mysqldb' in packages)
        self.assertTrue('python-pymysql' in packages)

    @patch.object(neutron_utils, 'git_install_requested')
    def test_get_packages_ovs_newton(self, git_requested):
        git_requested.return_value = False
        self.config.return_value = 'ovs'
        self.os_release.return_value = 'newton'
        packages = neutron_utils.get_packages()
        self.assertTrue('neutron-metering-agent' in packages)
        self.assertFalse('neutron-plugin-metering-agent' in packages)
        self.assertTrue('neutron-openvswitch-agent' in packages)
        self.assertFalse('neutron-plugin-openvswitch-agent' in packages)
        self.assertFalse('neutron-lbaas-agent' in packages)
        self.assertFalse('python-mysqldb' in packages)
        self.assertTrue('python-pymysql' in packages)

    @patch.object(neutron_utils, 'git_install_requested')
    def test_get_packages_ovsodl_icehouse(self, git_requested):
        git_requested.return_value = False
        self.config.return_value = 'ovs-odl'
        self.os_release.return_value = 'icehouse'
        packages = neutron_utils.get_packages()
        self.assertTrue('neutron-metering-agent' in packages)
        self.assertFalse('neutron-plugin-metering-agent' in packages)
        self.assertFalse('neutron-plugin-openvswitch-agent' in packages)
        self.assertFalse('neutron-openvswitch-agent' in packages)
        self.assertTrue('neutron-lbaas-agent' in packages)

    @patch.object(neutron_utils, 'git_install_requested')
    def test_get_packages_ovsodl_newton(self, git_requested):
        git_requested.return_value = False
        self.config.return_value = 'ovs-odl'
        self.os_release.return_value = 'newton'
        packages = neutron_utils.get_packages()
        self.assertTrue('neutron-metering-agent' in packages)
        self.assertFalse('neutron-plugin-metering-agent' in packages)
        self.assertFalse('neutron-plugin-openvswitch-agent' in packages)
        self.assertFalse('neutron-openvswitch-agent' in packages)
        self.assertFalse('neutron-lbaas-agent' in packages)
        self.assertTrue('neutron-lbaasv2-agent' in packages)

    @patch.object(neutron_utils, 'git_install_requested')
    def test_get_packages_l3ha(self, git_requested):
        git_requested.return_value = False
        self.config.return_value = 'ovs'
        self.get_os_codename_install_source.return_value = 'juno'
        self.assertTrue('keepalived' in neutron_utils.get_packages())

    @patch('charmhelpers.contrib.openstack.context.config')
    def test_configure_ovs_starts_service_if_required(self, mock_config):
        mock_config.side_effect = self.test_config.get
        self.config.return_value = 'ovs'
        self.service_running.return_value = False
        neutron_utils.configure_ovs()
        self.assertTrue(self.full_restart.called)

    def test_configure_ovs_doesnt_restart_service(self):
        self.service_running.return_value = True
        neutron_utils.configure_ovs()
        self.assertFalse(self.full_restart.called)

    @patch('charmhelpers.contrib.openstack.context.config')
    def test_configure_ovs_ovs_ext_port(self, mock_config):
        mock_config.side_effect = self.test_config.get
        self.config.side_effect = self.test_config.get
        self.test_config.set('plugin', 'ovs')
        self.test_config.set('ext-port', 'eth0')
        self.ExternalPortContext.return_value = \
            DummyExternalPortContext(return_value={'ext_port': 'eth0'})
        neutron_utils.configure_ovs()
        self.add_bridge.assert_has_calls([
            call('br-int'),
            call('br-ex'),
            call('br-data')
        ])
        self.add_bridge_port.assert_called_with('br-ex', 'eth0')

    @patch('charmhelpers.contrib.openstack.context.config')
    def test_configure_ovs_ovs_data_port(self, mock_config):
        mock_config.side_effect = self.test_config.get
        self.config.side_effect = self.test_config.get
        self.test_config.set('plugin', 'ovs')
        self.ExternalPortContext.return_value = \
            DummyExternalPortContext(return_value=None)
        # Test back-compatibility i.e. port but no bridge (so br-data is
        # assumed)
        self.test_config.set('data-port', 'eth0')
        neutron_utils.configure_ovs()
        self.add_bridge.assert_has_calls([
            call('br-int'),
            call('br-ex'),
            call('br-data')
        ])
        calls = [call('br-data', 'eth0', promisc=True)]
        self.add_bridge_port.assert_has_calls(calls)

        # Now test with bridge:port format and bogus bridge
        self.test_config.set('data-port', 'br-foo:eth0')
        self.add_bridge.reset_mock()
        self.add_bridge_port.reset_mock()
        neutron_utils.configure_ovs()
        self.add_bridge.assert_has_calls([
            call('br-int'),
            call('br-ex'),
            call('br-data')
        ])
        # Not called since we have a bogus bridge in data-ports
        self.assertFalse(self.add_bridge_port.called)

        # Now test with bridge:port format
        self.test_config.set('bridge-mappings', 'net1:br1')
        self.test_config.set('data-port', 'br1:eth0.100 br1:eth0.200')
        self.add_bridge.reset_mock()
        self.add_bridge_port.reset_mock()
        neutron_utils.configure_ovs()
        self.add_bridge.assert_has_calls([
            call('br-int'),
            call('br-ex'),
            call('br1')
        ])
        calls = [call('br1', 'eth0.100', promisc=True),
                 call('br1', 'eth0.200', promisc=True)]
        self.add_bridge_port.assert_has_calls(calls)

    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    @patch.object(neutron_utils, 'git_install_requested')
    def test_do_openstack_upgrade(self, git_requested, mock_renderer):
        git_requested.return_value = False
        self.config.side_effect = self.test_config.get
        self.is_relation_made.return_value = False
        self.test_config.set('openstack-origin', 'cloud:precise-havana')
        self.test_config.set('plugin', 'ovs')
        self.get_os_codename_install_source.return_value = 'havana'
        configs = neutron_utils.register_configs()
        neutron_utils.do_openstack_upgrade(configs)
        self.assertTrue(self.log.called)
        self.apt_update.assert_called_with(fatal=True)
        dpkg_opts = [
            '--option', 'Dpkg::Options::=--force-confnew',
            '--option', 'Dpkg::Options::=--force-confdef',
        ]
        self.apt_upgrade.assert_called_with(
            options=dpkg_opts, fatal=True, dist=True
        )
        self.configure_installation_source.assert_called_with(
            'cloud:precise-havana'
        )

    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_register_configs_ovs(self, mock_renderer):
        self.config.return_value = 'ovs'
        self.is_relation_made.return_value = False
        configs = neutron_utils.register_configs()
        confs = [neutron_utils.NEUTRON_DHCP_AGENT_CONF,
                 neutron_utils.NEUTRON_METADATA_AGENT_CONF,
                 neutron_utils.NOVA_CONF,
                 neutron_utils.NEUTRON_CONF,
                 neutron_utils.NEUTRON_L3_AGENT_CONF,
                 neutron_utils.NEUTRON_ML2_PLUGIN_CONF,
                 neutron_utils.EXT_PORT_CONF]
        for conf in confs:
            configs.register.assert_any_call(conf, ANY)

    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_register_configs_ovs_odl(self, mock_renderer):
        self.config.side_effect = self.test_config.get
        self.test_config.set('plugin', 'ovs-odl')
        self.is_relation_made.return_value = False
        self.get_os_codename_install_source.return_value = 'icehouse'
        configs = neutron_utils.register_configs()
        confs = [neutron_utils.NEUTRON_DHCP_AGENT_CONF,
                 neutron_utils.NEUTRON_METADATA_AGENT_CONF,
                 neutron_utils.NOVA_CONF,
                 neutron_utils.NEUTRON_CONF,
                 neutron_utils.NEUTRON_L3_AGENT_CONF,
                 neutron_utils.EXT_PORT_CONF]
        for conf in confs:
            configs.register.assert_any_call(conf, ANY)

    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_register_configs_amqp_nova(self, mock_renderer):
        self.config.return_value = 'ovs'
        self.is_relation_made.return_value = True
        configs = neutron_utils.register_configs()
        confs = [neutron_utils.NEUTRON_DHCP_AGENT_CONF,
                 neutron_utils.NEUTRON_METADATA_AGENT_CONF,
                 neutron_utils.NOVA_CONF,
                 neutron_utils.NEUTRON_CONF,
                 neutron_utils.NEUTRON_L3_AGENT_CONF,
                 neutron_utils.NEUTRON_ML2_PLUGIN_CONF,
                 neutron_utils.EXT_PORT_CONF]
        for conf in confs:
            configs.register.assert_any_call(conf, ANY)

    @patch.object(neutron_utils, 'get_packages')
    def test_restart_map_ovs(self, mock_get_packages):
        self.config.return_value = 'ovs'
        self.get_os_codename_install_source.return_value = 'havana'
        mock_get_packages.return_value = ['neutron-vpn-agent']
        self.os_release.return_value = 'icehouse'
        ex_map = {
            neutron_utils.NEUTRON_CONF: ['neutron-dhcp-agent',
                                         'neutron-metadata-agent',
                                         'neutron-plugin-openvswitch-agent',
                                         'neutron-metering-agent',
                                         'neutron-lbaas-agent',
                                         'neutron-vpn-agent'],
            neutron_utils.NEUTRON_DNSMASQ_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_LBAAS_AGENT_CONF:
            ['neutron-lbaas-agent'],
            neutron_utils.NEUTRON_ML2_PLUGIN_CONF:
            ['neutron-plugin-openvswitch-agent'],
            neutron_utils.NEUTRON_METADATA_AGENT_CONF:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_VPNAAS_AGENT_CONF: [
                'neutron-vpn-agent'],
            neutron_utils.NEUTRON_L3_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_DHCP_AGENT_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_FWAAS_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_METERING_AGENT_CONF:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_CONF: ['nova-api-metadata'],
            neutron_utils.EXT_PORT_CONF: ['ext-port'],
            neutron_utils.PHY_NIC_MTU_CONF: ['os-charm-phy-nic-mtu'],
            neutron_utils.NEUTRON_DHCP_AA_PROFILE_PATH: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_OVS_AA_PROFILE_PATH:
                ['neutron-plugin-openvswitch-agent'],
            neutron_utils.NEUTRON_L3_AA_PROFILE_PATH: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_LBAAS_AA_PROFILE_PATH:
            ['neutron-lbaas-agent'],
            neutron_utils.NEUTRON_METADATA_AA_PROFILE_PATH:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_METERING_AA_PROFILE_PATH:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_API_METADATA_AA_PROFILE_PATH:
            ['nova-api-metadata'],
        }

        self.assertDictEqual(neutron_utils.restart_map(), ex_map)

    @patch.object(neutron_utils, 'get_packages')
    def test_restart_map_ovs_mitaka(self, mock_get_packages):
        self.config.return_value = 'ovs'
        mock_get_packages.return_value = ['neutron-vpn-agent']
        self.os_release.return_value = 'mitaka'
        ex_map = {
            neutron_utils.NEUTRON_CONF: ['neutron-dhcp-agent',
                                         'neutron-metadata-agent',
                                         'neutron-openvswitch-agent',
                                         'neutron-metering-agent',
                                         'neutron-lbaas-agent',
                                         'neutron-vpn-agent'],
            neutron_utils.NEUTRON_DNSMASQ_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_LBAAS_AGENT_CONF:
            ['neutron-lbaas-agent'],
            neutron_utils.NEUTRON_OVS_AGENT_CONF:
            ['neutron-openvswitch-agent'],
            neutron_utils.NEUTRON_METADATA_AGENT_CONF:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_VPNAAS_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_L3_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_DHCP_AGENT_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_FWAAS_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_METERING_AGENT_CONF:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_CONF: ['nova-api-metadata'],
            neutron_utils.EXT_PORT_CONF: ['ext-port'],
            neutron_utils.PHY_NIC_MTU_CONF: ['os-charm-phy-nic-mtu'],
            neutron_utils.NEUTRON_DHCP_AA_PROFILE_PATH: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_OVS_AA_PROFILE_PATH:
                ['neutron-openvswitch-agent'],
            neutron_utils.NEUTRON_L3_AA_PROFILE_PATH: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_LBAAS_AA_PROFILE_PATH:
            ['neutron-lbaas-agent'],
            neutron_utils.NEUTRON_METADATA_AA_PROFILE_PATH:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_METERING_AA_PROFILE_PATH:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_API_METADATA_AA_PROFILE_PATH:
            ['nova-api-metadata'],
        }
        self.assertEqual(ex_map, neutron_utils.restart_map())

    @patch.object(neutron_utils, 'get_packages')
    def test_restart_map_ovs_newton(self, mock_get_packages):
        self.config.return_value = 'ovs'
        mock_get_packages.return_value = ['neutron-vpn-agent']
        self.os_release.return_value = 'newton'
        ex_map = {
            neutron_utils.NEUTRON_CONF: ['neutron-dhcp-agent',
                                         'neutron-metadata-agent',
                                         'neutron-openvswitch-agent',
                                         'neutron-metering-agent',
                                         'neutron-lbaasv2-agent',
                                         'neutron-vpn-agent'],
            neutron_utils.NEUTRON_DNSMASQ_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_LBAAS_AGENT_CONF:
            ['neutron-lbaasv2-agent'],
            neutron_utils.NEUTRON_OVS_AGENT_CONF:
            ['neutron-openvswitch-agent'],
            neutron_utils.NEUTRON_METADATA_AGENT_CONF:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_VPNAAS_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_L3_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_DHCP_AGENT_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_FWAAS_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_METERING_AGENT_CONF:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_CONF: ['nova-api-metadata'],
            neutron_utils.EXT_PORT_CONF: ['ext-port'],
            neutron_utils.PHY_NIC_MTU_CONF: ['os-charm-phy-nic-mtu'],
        }
        self.assertEqual(ex_map, neutron_utils.restart_map())

    @patch.object(neutron_utils, 'get_packages')
    def test_restart_map_ovs_post_trusty(self, mock_get_packages):
        self.config.return_value = 'ovs'
        # No VPN agent after trusty
        mock_get_packages.return_value = ['neutron-l3-agent']
        rmap = neutron_utils.restart_map()
        for services in rmap.itervalues():
            self.assertFalse('neutron-vpn-agent' in services)

    @patch.object(neutron_utils, 'get_packages')
    def test_restart_map_ovs_odl(self, mock_get_packages):
        self.config.return_value = 'ovs-odl'
        mock_get_packages.return_value = ['neutron-vpn-agent']
        self.os_release.return_value = 'icehouse'
        ex_map = {
            neutron_utils.NEUTRON_CONF: ['neutron-dhcp-agent',
                                         'neutron-metadata-agent',
                                         'neutron-metering-agent',
                                         'neutron-lbaas-agent',
                                         'neutron-vpn-agent'],
            neutron_utils.NEUTRON_DNSMASQ_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_LBAAS_AGENT_CONF:
            ['neutron-lbaas-agent'],
            neutron_utils.NEUTRON_METADATA_AGENT_CONF:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_VPNAAS_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_L3_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_DHCP_AGENT_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_FWAAS_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_METERING_AGENT_CONF:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_CONF: ['nova-api-metadata'],
            neutron_utils.EXT_PORT_CONF: ['ext-port'],
            neutron_utils.PHY_NIC_MTU_CONF: ['os-charm-phy-nic-mtu'],
            neutron_utils.NEUTRON_DHCP_AA_PROFILE_PATH: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_L3_AA_PROFILE_PATH: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_LBAAS_AA_PROFILE_PATH:
            ['neutron-lbaas-agent'],
            neutron_utils.NEUTRON_METADATA_AA_PROFILE_PATH:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_METERING_AA_PROFILE_PATH:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_API_METADATA_AA_PROFILE_PATH:
            ['nova-api-metadata'],
        }

        self.assertDictEqual(neutron_utils.restart_map(), ex_map)

    @patch.object(neutron_utils, 'get_packages')
    def test_restart_map_ovs_odl_newton(self, mock_get_packages):
        self.config.return_value = 'ovs-odl'
        mock_get_packages.return_value = ['neutron-vpn-agent']
        self.os_release.return_value = 'newton'
        ex_map = {
            neutron_utils.NEUTRON_CONF: ['neutron-dhcp-agent',
                                         'neutron-metadata-agent',
                                         'neutron-metering-agent',
                                         'neutron-lbaasv2-agent',
                                         'neutron-vpn-agent'],
            neutron_utils.NEUTRON_DNSMASQ_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_LBAAS_AGENT_CONF:
            ['neutron-lbaasv2-agent'],
            neutron_utils.NEUTRON_METADATA_AGENT_CONF:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_VPNAAS_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_L3_AGENT_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_DHCP_AGENT_CONF: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_FWAAS_CONF: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_METERING_AGENT_CONF:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_CONF: ['nova-api-metadata'],
            neutron_utils.EXT_PORT_CONF: ['ext-port'],
            neutron_utils.PHY_NIC_MTU_CONF: ['os-charm-phy-nic-mtu'],
            neutron_utils.NEUTRON_DHCP_AA_PROFILE_PATH: ['neutron-dhcp-agent'],
            neutron_utils.NEUTRON_L3_AA_PROFILE_PATH: ['neutron-vpn-agent'],
            neutron_utils.NEUTRON_LBAASV2_AA_PROFILE_PATH:
            ['neutron-lbaasv2-agent'],
            neutron_utils.NEUTRON_METADATA_AA_PROFILE_PATH:
            ['neutron-metadata-agent'],
            neutron_utils.NEUTRON_METERING_AA_PROFILE_PATH:
            ['neutron-metering-agent'],
            neutron_utils.NOVA_API_METADATA_AA_PROFILE_PATH:
            ['nova-api-metadata'],
        }

        self.assertEqual(neutron_utils.restart_map(), ex_map)

    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_register_configs_nsx(self, mock_renderer):
        self.config.return_value = 'nsx'
        configs = neutron_utils.register_configs()
        confs = [neutron_utils.NEUTRON_DHCP_AGENT_CONF,
                 neutron_utils.NEUTRON_METADATA_AGENT_CONF,
                 neutron_utils.NOVA_CONF,
                 neutron_utils.NEUTRON_CONF]
        for conf in confs:
            configs.register.assert_any_call(conf, ANY)

    def test_stop_services_ovs(self):
        self.config.return_value = 'ovs'
        neutron_utils.stop_services()
        calls = [call('neutron-dhcp-agent'),
                 call('neutron-plugin-openvswitch-agent'),
                 call('nova-api-metadata'),
                 call('neutron-l3-agent'),
                 call('neutron-metadata-agent')]
        self.service_stop.assert_has_calls(
            calls,
            any_order=True,
        )

    @patch('charmhelpers.contrib.openstack.templating.OSConfigRenderer')
    def test_register_configs_pre_install(self, mock_renderer):
        self.config.return_value = 'ovs'
        self.is_relation_made.return_value = False
        configs = neutron_utils.register_configs()
        confs = [neutron_utils.NOVA_CONF,
                 neutron_utils.NEUTRON_CONF,
                 neutron_utils.NEUTRON_L3_AGENT_CONF,
                 neutron_utils.NEUTRON_ML2_PLUGIN_CONF,
                 neutron_utils.EXT_PORT_CONF]
        for conf in confs:
            configs.register.assert_any_call(conf, ANY)

    def test_copy_file_without_update(self):
        src = 'dummy_source_dir/dummy_file'
        dst = 'dummy_des_dir'
        neutron_utils.copy_file(src, dst)
        self.assertTrue(self.mkdir.called)
        self.assertTrue(self.copy2.called)

    @patch('neutron_utils.os.path.isfile')
    def test_copy_file_with_update(self, _isfile):
        src = 'dummy_source_dir/dummy_file'
        dst = 'dummy_des_dir'
        _isfile.return_value = False
        neutron_utils.copy_file(src, dst, force=True)
        self.assertTrue(self.mkdir.called)
        self.assertTrue(self.copy2.called)

    @patch('neutron_utils.os.remove')
    @patch('neutron_utils.os.path.isfile')
    def test_remove_file_exists(self, _isfile, _remove):
        path = 'dummy_des_dir/dummy_file'
        _isfile.return_value = True
        neutron_utils.remove_file(path)
        self.assertTrue(_remove.called)
        self.assertFalse(self.log.called)

    @patch('neutron_utils.os.remove')
    @patch('neutron_utils.os.path.isfile')
    def test_remove_file_non_exists(self, _isfile, _remove):
        path = 'dummy_des_dir/dummy_file'
        _isfile.return_value = False
        neutron_utils.remove_file(path)
        self.assertFalse(_remove.called)
        self.assertTrue(self.log.called)

    def test_resolve_config_files_ovs_liberty(self):
        self._set_distrib_codename('trusty')
        self.os_release.return_value = 'liberty'
        self.is_relation_made = False
        actual_map = neutron_utils.resolve_config_files(neutron_utils.OVS,
                                                        'liberty')
        actual_configs = actual_map[neutron_utils.OVS].keys()
        INC_CONFIG = [neutron_utils.NEUTRON_ML2_PLUGIN_CONF]
        EXC_CONFIG = [neutron_utils.NEUTRON_OVS_AGENT_CONF,
                      neutron_utils.NEUTRON_LBAASV2_AA_PROFILE_PATH]
        for config in INC_CONFIG:
            self.assertTrue(config in actual_configs)
        for config in EXC_CONFIG:
            self.assertTrue(config not in actual_configs)

    def test_resolve_config_files_ovs_mitaka(self):
        self._set_distrib_codename('trusty')
        self.os_release.return_value = 'mitaka'
        self.is_relation_made = False
        actual_map = neutron_utils.resolve_config_files(neutron_utils.OVS,
                                                        'mitaka')
        actual_configs = actual_map[neutron_utils.OVS].keys()
        INC_CONFIG = [neutron_utils.NEUTRON_OVS_AGENT_CONF]
        EXC_CONFIG = [neutron_utils.NEUTRON_ML2_PLUGIN_CONF,
                      neutron_utils.NEUTRON_LBAASV2_AA_PROFILE_PATH]
        for config in INC_CONFIG:
            self.assertTrue(config in actual_configs)
        for config in EXC_CONFIG:
            self.assertTrue(config not in actual_configs)

    def test_resolve_config_files_ovs_trusty(self):
        self._set_distrib_codename('trusty')
        self.os_release.return_value = 'mitaka'
        self.is_relation_made = False
        actual_map = neutron_utils.resolve_config_files(neutron_utils.OVS,
                                                        'mitaka')
        actual_configs = actual_map[neutron_utils.OVS].keys()
        INC_CONFIG = [neutron_utils.EXT_PORT_CONF,
                      neutron_utils.PHY_NIC_MTU_CONF,
                      neutron_utils.NEUTRON_LBAAS_AA_PROFILE_PATH]
        for config in INC_CONFIG:
            self.assertTrue(config in actual_configs)

    def test_resolve_config_files_ovs_xenial(self):
        self._set_distrib_codename('xenial')
        self.os_release.return_value = 'mitaka'
        self.is_relation_made = False
        actual_map = neutron_utils.resolve_config_files(neutron_utils.OVS,
                                                        'mitaka')
        actual_configs = actual_map[neutron_utils.OVS].keys()
        EXC_CONFIG = [neutron_utils.EXT_PORT_CONF,
                      neutron_utils.PHY_NIC_MTU_CONF,
                      neutron_utils.NEUTRON_LBAASV2_AA_PROFILE_PATH]
        for config in EXC_CONFIG:
            self.assertTrue(config not in actual_configs)

    def test_resolve_config_files_ovs_newton(self):
        self._set_distrib_codename('xenial')
        self.os_release.return_value = 'newton'
        self.is_relation_made = False
        actual_map = neutron_utils.resolve_config_files(neutron_utils.OVS,
                                                        'newton')
        actual_configs = actual_map[neutron_utils.OVS].keys()
        EXC_CONFIG = [neutron_utils.EXT_PORT_CONF,
                      neutron_utils.PHY_NIC_MTU_CONF,
                      neutron_utils.NEUTRON_LBAAS_AA_PROFILE_PATH]
        for config in EXC_CONFIG:
            self.assertTrue(config not in actual_configs)


network_context = {
    'service_username': 'foo',
    'service_password': 'bar',
    'service_tenant': 'baz',
    'region': 'foo-bar',
    'keystone_host': 'keystone',
    'auth_port': 5000,
    'auth_protocol': 'https'
}


class DummyNetworkServiceContext():

    def __init__(self, return_value):
        self.return_value = return_value

    def __call__(self):
        return self.return_value


class DummyExternalPortContext():

    def __init__(self, return_value):
        self.return_value = return_value

    def __call__(self):
        return self.return_value

agents_all_alive = {
    'DHCP Agent': {
        'agents': [
            {'alive': True,
             'host': 'cluster1-machine1.internal',
             'id': '3e3550f2-38cc-11e3-9617-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster1-machine2.internal',
             'id': '53d6eefc-38cc-11e3-b3c8-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine1.internal',
             'id': '92b8b6bc-38ce-11e3-8537-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine3.internal',
             'id': 'ebdcc950-51c8-11e3-a804-1c6f65b044df'},
        ]
    },
    'L3 Agent': {
        'agents': [
            {'alive': True,
             'host': 'cluster1-machine1.internal',
             'id': '7128198e-38ce-11e3-ba78-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster1-machine2.internal',
             'id': '72453824-38ce-11e3-938e-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine1.internal',
             'id': '84a04126-38ce-11e3-9449-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine3.internal',
             'id': '00f4268a-51c9-11e3-9177-1c6f65b044df'},
        ]
    }
}

agents_some_dead_cl1 = {
    'DHCP Agent': {
        'agents': [
            {'alive': False,
             'host': 'cluster1-machine1.internal',
             'id': '3e3550f2-38cc-11e3-9617-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine1.internal',
             'id': '53d6eefc-38cc-11e3-b3c8-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine2.internal',
             'id': '92b8b6bc-38ce-11e3-8537-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine3.internal',
             'id': 'ebdcc950-51c8-11e3-a804-1c6f65b044df'},
        ]
    },
    'L3 Agent': {
        'agents': [
            {'alive': False,
             'host': 'cluster1-machine1.internal',
             'id': '7128198e-38ce-11e3-ba78-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine1.internal',
             'id': '72453824-38ce-11e3-938e-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine2.internal',
             'id': '84a04126-38ce-11e3-9449-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine3.internal',
             'id': '00f4268a-51c9-11e3-9177-1c6f65b044df'},
        ]
    }
}

agents_some_dead_cl2 = {
    'DHCP Agent': {
        'agents': [
            {'alive': True,
             'host': 'cluster1-machine1.internal',
             'id': '3e3550f2-38cc-11e3-9617-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine1.internal',
             'id': '53d6eefc-38cc-11e3-b3c8-3c970e8b1cf7'},
            {'alive': False,
             'host': 'cluster2-machine2.internal',
             'id': '92b8b6bc-38ce-11e3-8537-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine3.internal',
             'id': 'ebdcc950-51c8-11e3-a804-1c6f65b044df'},
        ]
    },
    'L3 Agent': {
        'agents': [
            {'alive': True,
             'host': 'cluster1-machine1.internal',
             'id': '7128198e-38ce-11e3-ba78-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine1.internal',
             'id': '72453824-38ce-11e3-938e-3c970e8b1cf7'},
            {'alive': False,
             'host': 'cluster2-machine2.internal',
             'id': '84a04126-38ce-11e3-9449-3c970e8b1cf7'},
            {'alive': True,
             'host': 'cluster2-machine3.internal',
             'id': '00f4268a-51c9-11e3-9177-1c6f65b044df'},
        ]
    }
}

dhcp_agent_networks = {
    'networks': [
        {'id': 'foo'},
        {'id': 'bar'}
    ]
}

l3_agent_routers = {
    'routers': [
        {'id': 'baz'},
        {'id': 'bong'}
    ]
}

cluster1 = ['cluster1-machine1.internal']
cluster2 = ['cluster2-machine1.internal', 'cluster2-machine2.internal'
            'cluster2-machine3.internal']


class TestNeutronAgentReallocation(CharmTestCase):

    def setUp(self):
        if not neutronclient:
            raise self.skipTest('Skipping, no neutronclient installed')
        super(TestNeutronAgentReallocation, self).setUp(neutron_utils,
                                                        TO_PATCH)

    def tearDown(self):
        # Reset cached cache
        hookenv.cache = {}

    def test_no_network_context(self):
        self.NetworkServiceContext.return_value = \
            DummyNetworkServiceContext(return_value=None)
        neutron_utils.reassign_agent_resources()
        self.assertTrue(self.log.called)

    @patch('neutronclient.v2_0.client.Client')
    def test_no_down_agents(self, _client):
        self.NetworkServiceContext.return_value = \
            DummyNetworkServiceContext(return_value=network_context)
        dummy_client = MagicMock()
        dummy_client.list_agents.side_effect = agents_all_alive.itervalues()
        _client.return_value = dummy_client
        neutron_utils.reassign_agent_resources()
        dummy_client.add_router_to_l3_agent.assert_not_called()
        dummy_client.remove_router_from_l3_agent.assert_not_called()
        dummy_client.add_network_to_dhcp_agent.assert_not_called()
        dummy_client.remove_network_from_dhcp_agent.assert_not_called()

    @patch('neutronclient.v2_0.client.Client')
    def test_agents_down_relocation_required(self, _client):
        self.NetworkServiceContext.return_value = \
            DummyNetworkServiceContext(return_value=network_context)
        dummy_client = MagicMock()
        dummy_client.list_agents.side_effect = \
            agents_some_dead_cl2.itervalues()
        dummy_client.list_networks_on_dhcp_agent.return_value = \
            dhcp_agent_networks
        dummy_client.list_routers_on_l3_agent.return_value = \
            l3_agent_routers
        _client.return_value = dummy_client
        self.unit_private_ip.return_value = 'cluster2-machine1.internal'
        self.relations_of_type.return_value = \
            [{'private-address': 'cluster2-machine3.internal'}]
        neutron_utils.reassign_agent_resources()

        # Ensure routers removed from dead l3 agent
        dummy_client.remove_router_from_l3_agent.assert_has_calls(
            [call(l3_agent='84a04126-38ce-11e3-9449-3c970e8b1cf7',
                  router_id='bong'),
             call(l3_agent='84a04126-38ce-11e3-9449-3c970e8b1cf7',
                  router_id='baz')], any_order=True)
        # and re-assigned across the remaining two live agents
        dummy_client.add_router_to_l3_agent.assert_has_calls(
            [call(l3_agent='00f4268a-51c9-11e3-9177-1c6f65b044df',
                  body={'router_id': 'baz'}),
             call(l3_agent='72453824-38ce-11e3-938e-3c970e8b1cf7',
                  body={'router_id': 'bong'})], any_order=True)
        # Ensure networks removed from dead dhcp agent
        dummy_client.remove_network_from_dhcp_agent.assert_has_calls(
            [call(dhcp_agent='92b8b6bc-38ce-11e3-8537-3c970e8b1cf7',
                  network_id='foo'),
             call(dhcp_agent='92b8b6bc-38ce-11e3-8537-3c970e8b1cf7',
                  network_id='bar')], any_order=True)
        # and re-assigned across the remaining two live agents
        dummy_client.add_network_to_dhcp_agent.assert_has_calls(
            [call(dhcp_agent='53d6eefc-38cc-11e3-b3c8-3c970e8b1cf7',
                  body={'network_id': 'foo'}),
             call(dhcp_agent='ebdcc950-51c8-11e3-a804-1c6f65b044df',
                  body={'network_id': 'bar'})], any_order=True)

    @patch('neutronclient.v2_0.client.Client')
    def test_agents_down_relocation_impossible(self, _client):
        self.NetworkServiceContext.return_value = \
            DummyNetworkServiceContext(return_value=network_context)
        dummy_client = MagicMock()
        dummy_client.list_agents.side_effect = \
            agents_some_dead_cl1.itervalues()
        dummy_client.list_networks_on_dhcp_agent.return_value = \
            dhcp_agent_networks
        dummy_client.list_routers_on_l3_agent.return_value = \
            l3_agent_routers
        _client.return_value = dummy_client
        self.unit_private_ip.return_value = 'cluster1-machine1.internal'
        self.relations_of_type.return_value = []
        neutron_utils.reassign_agent_resources()
        self.assertTrue(self.log.called)
        assert not dummy_client.remove_router_from_l3_agent.called
        assert not dummy_client.remove_network_from_dhcp_agent.called

    @patch.object(neutron_utils, 'git_install_requested')
    @patch.object(neutron_utils, 'git_clone_and_install')
    @patch.object(neutron_utils, 'git_post_install')
    @patch.object(neutron_utils, 'git_pre_install')
    def test_git_install(self, git_pre, git_post, git_clone_and_install,
                         git_requested):
        projects_yaml = openstack_origin_git
        git_requested.return_value = True
        neutron_utils.git_install(projects_yaml)
        self.assertTrue(git_pre.called)
        git_clone_and_install.assert_called_with(openstack_origin_git,
                                                 core_project='neutron')
        self.assertTrue(git_post.called)

    @patch('subprocess.check_call')
    @patch.object(neutron_utils, 'mkdir')
    @patch.object(neutron_utils, 'write_file')
    @patch.object(neutron_utils, 'add_user_to_group')
    @patch.object(neutron_utils, 'add_group')
    @patch.object(neutron_utils, 'adduser')
    def test_git_pre_install(self, adduser, add_group, add_user_to_group,
                             write_file, mkdir, check_call):
        neutron_utils.git_pre_install()
        expected = [
            call('neutron', shell='/bin/bash', system_user=True),
            call('nova', shell='/bin/bash', system_user=True),
        ]
        self.assertEquals(adduser.call_args_list, expected)
        expected = [
            call('neutron', system_group=True),
            call('nova', system_group=True),
        ]
        self.assertEquals(add_group.call_args_list, expected)
        expected = [
            call('neutron', 'neutron'),
            call('nova', 'nova'),
        ]
        self.assertEquals(add_user_to_group.call_args_list, expected)
        expected = [
            call('/etc/neutron', owner='neutron',
                 group='neutron', perms=0755, force=False),
            call('/etc/neutron/rootwrap.d', owner='neutron',
                 group='neutron', perms=0755, force=False),
            call('/etc/neutron/plugins', owner='neutron',
                 group='neutron', perms=0755, force=False),
            call('/etc/nova', owner='neutron',
                 group='neutron', perms=0755, force=False),
            call('/var/lib/neutron', owner='neutron',
                 group='neutron', perms=0755, force=False),
            call('/var/lib/neutron/lock', owner='neutron',
                 group='neutron', perms=0755, force=False),
            call('/var/log/neutron', owner='neutron',
                 group='neutron', perms=0755, force=False),
            call('/var/lib/nova', owner='neutron',
                 group='neutron', perms=0755, force=False),
            call('/var/log/nova', owner='neutron',
                 group='neutron', perms=0755, force=False),
        ]
        self.assertEquals(mkdir.call_args_list, expected)
        expected = [
            call('/var/log/neutron/bigswitch-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/dhcp-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/l3-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/lbaas-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/ibm-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/linuxbridge-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/metadata-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/metering_agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/mlnx-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/nec-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/nvsd-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/openflow-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/openvswitch-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/ovs-cleanup.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/ryu-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/server.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/sriov-agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
            call('/var/log/neutron/vpn_agent.log', '', owner='neutron',
                 group='neutron', perms=0644),
        ]
        self.assertEquals(write_file.call_args_list, expected)

    @patch('os.remove')
    @patch('os.path.join')
    @patch('os.path.exists')
    @patch('os.symlink')
    @patch('shutil.rmtree')
    @patch('shutil.copyfile')
    @patch('shutil.copytree')
    def test_git_post_install_upstart(self, copytree, copyfile, rmtree,
                                      symlink, exists, join, remove):
        projects_yaml = openstack_origin_git
        join.return_value = 'joined-string'
        self.lsb_release.return_value = {'DISTRIB_RELEASE': '15.04'}
        self.os_release.return_value = 'liberty'
        neutron_utils.git_post_install(projects_yaml)
        expected = [
            call('joined-string', '/etc/neutron'),
            call('joined-string', '/etc/neutron/plugins'),
            call('joined-string', '/etc/neutron/rootwrap.d'),
        ]
        copytree.assert_has_calls(expected)
        expected = [
            call('/usr/local/bin/neutron-rootwrap',
                 '/usr/bin/neutron-rootwrap'),
        ]
        symlink.assert_has_calls(expected)
        service_name = 'quantum-gateway'
        user_name = 'neutron'
        neutron_api_context = {
            'service_description': 'Neutron API server',
            'charm_name': 'neutron-api',
            'process_name': 'neutron-server',
            'executable_name': 'joined-string',
        }
        neutron_dhcp_agent_context = {
            'service_description': 'Neutron DHCP Agent',
            'service_name': service_name,
            'process_name': 'neutron-dhcp-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/dhcp_agent.ini'],
            'log_file': '/var/log/neutron/dhcp-agent.log',
        }
        neutron_l3_agent_context = {
            'service_description': 'Neutron L3 Agent',
            'service_name': service_name,
            'process_name': 'neutron-l3-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/l3_agent.ini',
                             '/etc/neutron/fwaas_driver.ini'],
            'log_file': '/var/log/neutron/l3-agent.log',
        }
        neutron_lbaas_agent_context = {
            'service_description': 'Neutron LBaaS Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-lbaas-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/lbaas_agent.ini'],
            'log_file': '/var/log/neutron/lbaas-agent.log',
        }
        neutron_metadata_agent_context = {
            'service_description': 'Neutron Metadata Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-metadata-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/metadata_agent.ini'],
            'log_file': '/var/log/neutron/metadata-agent.log',
        }
        neutron_metering_agent_context = {
            'service_description': 'Neutron Metering Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-metering-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/metering_agent.ini'],
            'log_file': '/var/log/neutron/metering-agent.log',
        }
        neutron_ovs_cleanup_context = {
            'service_description': 'Neutron OVS cleanup',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-ovs-cleanup',
            'executable_name': 'joined-string',
            'config_file': '/etc/neutron/neutron.conf',
            'log_file': '/var/log/neutron/ovs-cleanup.log',
        }
        neutron_plugin_bigswitch_context = {
            'service_description': 'Neutron BigSwitch Plugin Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-restproxy-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/plugins/bigswitch/restproxy.ini'],
            'log_file': '/var/log/neutron/bigswitch-agent.log',
        }
        neutron_plugin_ibm_context = {
            'service_description': 'Neutron IBM SDN Plugin Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-ibm-agent',
            'executable_name': 'joined-string',
            'config_files':
            ['/etc/neutron/neutron.conf',
             '/etc/neutron/plugins/ibm/sdnve_neutron_plugin.ini'],
            'log_file': '/var/log/neutron/ibm-agent.log',
        }
        neutron_plugin_linuxbridge_context = {
            'service_description': 'Neutron Linux Bridge Plugin Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-linuxbridge-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/plugins/ml2/ml2_conf.ini'],
            'log_file': '/var/log/neutron/linuxbridge-agent.log',
        }
        neutron_plugin_mlnx_context = {
            'service_description': 'Neutron MLNX Plugin Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-mlnx-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/plugins/mlnx/mlnx_conf.ini'],
            'log_file': '/var/log/neutron/mlnx-agent.log',
        }
        neutron_plugin_nec_context = {
            'service_description': 'Neutron NEC Plugin Agent',
            'service_name': service_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-nec-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/plugins/nec/nec.ini'],
            'log_file': '/var/log/neutron/nec-agent.log',
        }
        neutron_plugin_oneconvergence_context = {
            'service_description': 'Neutron One Convergence Plugin Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-nvsd-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/plugins/oneconvergence/'
                             'nvsdplugin.ini'],
            'log_file': '/var/log/neutron/nvsd-agent.log',
        }
        neutron_plugin_openflow_context = {
            'service_description': 'Neutron OpenFlow Plugin Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-ofagent-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/plugins/ml2/ml2_conf_ofa.ini'],
            'log_file': '/var/log/neutron/openflow-agent.log',
        }
        neutron_plugin_openvswitch_context = {
            'service_description': 'Neutron OpenvSwitch Plugin Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-openvswitch-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/plugins/ml2/ml2_conf.ini'],
            'log_file': '/var/log/neutron/openvswitch-agent.log',
        }
        neutron_plugin_ryu_context = {
            'service_description': 'Neutron RYU Plugin Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-ryu-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/plugins/ryu/ryu.ini'],
            'log_file': '/var/log/neutron/ryu-agent.log',
        }
        neutron_plugin_sriov_context = {
            'service_description': 'Neutron SRIOV SDN Plugin Agent',
            'service_name': service_name,
            'user_name': user_name,
            'start_dir': '/var/lib/neutron',
            'process_name': 'neutron-sriov-nic-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/plugins/ml2/ml2_conf_sriov'],
            'log_file': '/var/log/neutron/sriov-agent.log',
        }
        neutron_api_context = {
            'service_description': 'Neutron API server',
            'service_name': service_name,
            'process_name': 'neutron-server',
            'executable_name': 'joined-string',
        }
        neutron_vpn_agent_context = {
            'service_description': 'Neutron VPN Agent',
            'service_name': service_name,
            'process_name': 'neutron-vpn-agent',
            'executable_name': 'joined-string',
            'config_files': ['/etc/neutron/neutron.conf',
                             '/etc/neutron/vpn_agent.ini',
                             '/etc/neutron/l3_agent.ini',
                             '/etc/neutron/fwaas_driver.ini'],
            'log_file': '/var/log/neutron/vpn_agent.log',
        }
        nova_api_metadata_context = {
            'service_description': 'Nova Metadata API server',
            'service_name': 'nova-compute',
            'user_name': 'nova',
            'start_dir': '/var/lib/nova',
            'process_name': 'nova-api-metadata',
            'executable_name': 'joined-string',
            'config_files': ['/etc/nova/nova.conf'],
        }

        expected = [
            call('git/neutron_sudoers',
                 '/etc/sudoers.d/neutron_sudoers',
                 {}, perms=0o440),
            call('git/nova_sudoers',
                 '/etc/sudoers.d/nova_sudoers',
                 {}, perms=0o440),
            call('git/cron.d/neutron-dhcp-agent-netns-cleanup',
                 '/etc/cron.d/neutron-dhcp-agent-netns-cleanup',
                 {}, perms=0o755),
            call('git/cron.d/neutron-l3-agent-netns-cleanup',
                 '/etc/cron.d/neutron-l3-agent-netns-cleanup',
                 {}, perms=0o755),
            call('git/cron.d/neutron-lbaas-agent-netns-cleanup',
                 '/etc/cron.d/neutron-lbaas-agent-netns-cleanup',
                 {}, perms=0o755),
            call('git/upstart/neutron-agent.upstart',
                 '/etc/init/neutron-dhcp-agent.conf',
                 neutron_dhcp_agent_context, perms=0o644),
            call('git/upstart/neutron-agent.upstart',
                 '/etc/init/neutron-l3-agent.conf',
                 neutron_l3_agent_context, perms=0o644),
            call('git.upstart',
                 '/etc/init/neutron-lbaas-agent.conf',
                 neutron_lbaas_agent_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-metadata-agent.conf',
                 neutron_metadata_agent_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-metering-agent.conf',
                 neutron_metering_agent_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-ovs-cleanup.conf',
                 neutron_ovs_cleanup_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-plugin-bigswitch-agent.conf',
                 neutron_plugin_bigswitch_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-plugin-ibm-agent.conf',
                 neutron_plugin_ibm_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-plugin-linuxbridge-agent.conf',
                 neutron_plugin_linuxbridge_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-plugin-mlnx-agent.conf',
                 neutron_plugin_mlnx_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-plugin-nec-agent.conf',
                 neutron_plugin_nec_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-plugin-oneconvergence-agent.conf',
                 neutron_plugin_oneconvergence_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-plugin-openflow-agent.conf',
                 neutron_plugin_openflow_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-plugin-openvswitch-agent.conf',
                 neutron_plugin_openvswitch_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-plugin-ryu-agent.conf',
                 neutron_plugin_ryu_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git.upstart',
                 '/etc/init/neutron-plugin-sriov-agent.conf',
                 neutron_plugin_sriov_context, perms=0o644,
                 templates_dir='joined-string'),
            call('git/upstart/neutron-server.upstart',
                 '/etc/init/neutron-server.conf',
                 neutron_api_context, perms=0o644),
            call('git/upstart/neutron-agent.upstart',
                 '/etc/init/neutron-vpn-agent.conf',
                 neutron_vpn_agent_context, perms=0o644),
            call('git.upstart',
                 '/etc/init/nova-api-metadata.conf',
                 nova_api_metadata_context, perms=0o644,
                 templates_dir='joined-string'),
        ]
        self.assertEquals(self.render.call_args_list, expected)

    @patch('os.listdir')
    @patch('os.remove')
    @patch('os.path.join')
    @patch('os.path.exists')
    @patch('os.symlink')
    @patch('shutil.rmtree')
    @patch('shutil.copyfile')
    @patch('shutil.copytree')
    def test_git_post_install_systemd(self, copytree, copyfile, rmtree,
                                      symlink, exists, join, remove, listdir):
        projects_yaml = openstack_origin_git
        join.return_value = 'joined-string'
        self.lsb_release.return_value = {'DISTRIB_RELEASE': '15.10'}
        self.os_release.return_value = 'newton'
        neutron_utils.git_post_install(projects_yaml)

        expected = [
            call('git/neutron_sudoers',
                 '/etc/sudoers.d/neutron_sudoers',
                 {}, perms=288),
            call('git/nova_sudoers',
                 '/etc/sudoers.d/nova_sudoers',
                 {}, perms=288),
            call('git/cron.d/neutron-dhcp-agent-netns-cleanup',
                 '/etc/cron.d/neutron-dhcp-agent-netns-cleanup',
                 {}, perms=493),
            call('git/cron.d/neutron-l3-agent-netns-cleanup',
                 '/etc/cron.d/neutron-l3-agent-netns-cleanup',
                 {}, perms=493),
            call('git/cron.d/neutron-lbaas-agent-netns-cleanup',
                 '/etc/cron.d/neutron-lbaas-agent-netns-cleanup',
                 {}, perms=493),
            call('git/neutron-dhcp-agent.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-l3-agent.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-lbaasv2-agent.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-linuxbridge-agent.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-linuxbridge-cleanup.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-macvtap-agent.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-metadata-agent.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-metering-agent.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-openvswitch-agent.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-ovs-cleanup.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-server.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-sriov-agent.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/neutron-vpn-agent.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
            call('git/nova-api-metadata.init.in.template',
                 'joined-string', {'daemon_path': 'joined-string'},
                 perms=420),
        ]
        self.assertEquals(self.render.call_args_list, expected)

    def test_assess_status(self):
        with patch.object(neutron_utils, 'assess_status_func') as asf:
            callee = MagicMock()
            asf.return_value = callee
            neutron_utils.assess_status('test-config')
            asf.assert_called_once_with('test-config')
            callee.assert_called_once_with()
            self.os_application_version_set.assert_called_with(
                neutron_utils.VERSION_PACKAGE
            )

    @patch.object(neutron_utils, 'get_optional_interfaces')
    @patch.object(neutron_utils, 'check_optional_relations')
    @patch.object(neutron_utils, 'REQUIRED_INTERFACES')
    @patch.object(neutron_utils, 'services')
    @patch.object(neutron_utils, 'make_assess_status_func')
    def test_assess_status_func(self,
                                make_assess_status_func,
                                services,
                                REQUIRED_INTERFACES,
                                check_optional_relations,
                                get_optional_interfaces):
        services.return_value = ['s1']
        REQUIRED_INTERFACES.copy.return_value = {'int': ['test 1']}
        get_optional_interfaces.return_value = {'opt': ['test 2']}
        neutron_utils.assess_status_func('test-config')
        # ports=None whilst port checks are disabled.
        make_assess_status_func.assert_called_once_with(
            'test-config',
            {'int': ['test 1'], 'opt': ['test 2']},
            charm_func=check_optional_relations, services=['s1'], ports=None)

    def test_pause_unit_helper(self):
        with patch.object(neutron_utils, '_pause_resume_helper') as prh:
            neutron_utils.pause_unit_helper('random-config')
            prh.assert_called_once_with(neutron_utils.pause_unit,
                                        'random-config')
        with patch.object(neutron_utils, '_pause_resume_helper') as prh:
            neutron_utils.resume_unit_helper('random-config')
            prh.assert_called_once_with(neutron_utils.resume_unit,
                                        'random-config')

    @patch.object(neutron_utils, 'services')
    def test_pause_resume_helper(self, services):
        f = MagicMock()
        services.return_value = ['s1']
        with patch.object(neutron_utils, 'assess_status_func') as asf:
            asf.return_value = 'assessor'
            neutron_utils._pause_resume_helper(f, 'some-config')
            asf.assert_called_once_with('some-config')
            # ports=None whilst port checks are disabled.
            f.assert_called_once_with('assessor', services=['s1'], ports=None)

    @patch.object(neutron_utils, 'subprocess')
    @patch.object(neutron_utils, 'shutil')
    @patch('os.path.exists')
    def test_install_systemd_override_systemd(self, _os_exists, _shutil,
                                              _subprocess):
        '''
        Ensure systemd override is only installed on systemd based systems
        '''
        self.init_is_systemd.return_value = True
        _os_exists.return_value = False
        neutron_utils.install_systemd_override()
        _os_exists.assert_called_with(
            '/etc/systemd/system/nova-api-metadata.service.d/override.conf'
        )
        self.mkdir.assert_called_with(
            '/etc/systemd/system/nova-api-metadata.service.d'
        )
        _shutil.copy.assert_called_with(
            'files/override.conf',
            '/etc/systemd/system/nova-api-metadata.service.d/override.conf'
        )
        _subprocess.check_call.assert_called_with(
            ['systemctl', 'daemon-reload']
        )
