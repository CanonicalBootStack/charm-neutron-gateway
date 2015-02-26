# vim: set ts=4:et
import os
import uuid
import socket
from charmhelpers.core.host import (
    list_nics,
    get_nic_hwaddr
)
from charmhelpers.core.hookenv import (
    config,
    relation_ids,
    related_units,
    relation_get,
    unit_get,
    cached
)
from charmhelpers.fetch import (
    apt_install,
)
from charmhelpers.contrib.openstack.context import (
    OSContextGenerator,
    context_complete,
)
from charmhelpers.contrib.openstack.utils import (
    get_os_codename_install_source
)
from charmhelpers.contrib.hahelpers.cluster import(
    eligible_leader
)
import re
from charmhelpers.contrib.network.ip import (
    get_address_in_network,
    get_ipv4_addr,
    get_ipv6_addr,
    is_bridge_member,
)
from charmhelpers.core.strutils import bool_from_string

DB_USER = "quantum"
QUANTUM_DB = "quantum"
NOVA_DB_USER = "nova"
NOVA_DB = "nova"

QUANTUM_OVS_PLUGIN = \
    "quantum.plugins.openvswitch.ovs_quantum_plugin.OVSQuantumPluginV2"
QUANTUM_NVP_PLUGIN = \
    "quantum.plugins.nicira.nicira_nvp_plugin.QuantumPlugin.NvpPluginV2"
NEUTRON_OVS_PLUGIN = \
    "neutron.plugins.openvswitch.ovs_neutron_plugin.OVSNeutronPluginV2"
NEUTRON_ML2_PLUGIN = \
    "neutron.plugins.ml2.plugin.Ml2Plugin"
NEUTRON_NVP_PLUGIN = \
    "neutron.plugins.nicira.nicira_nvp_plugin.NeutronPlugin.NvpPluginV2"
NEUTRON_N1KV_PLUGIN = \
    "neutron.plugins.cisco.n1kv.n1kv_neutron_plugin.N1kvNeutronPluginV2"
NEUTRON_NSX_PLUGIN = "vmware"

NEUTRON = 'neutron'
QUANTUM = 'quantum'


def networking_name():
    ''' Determine whether neutron or quantum should be used for name '''
    if get_os_codename_install_source(config('openstack-origin')) >= 'havana':
        return NEUTRON
    else:
        return QUANTUM

OVS = 'ovs'
NVP = 'nvp'
N1KV = 'n1kv'
NSX = 'nsx'

CORE_PLUGIN = {
    QUANTUM: {
        OVS: QUANTUM_OVS_PLUGIN,
        NVP: QUANTUM_NVP_PLUGIN,
    },
    NEUTRON: {
        OVS: NEUTRON_OVS_PLUGIN,
        NVP: NEUTRON_NVP_PLUGIN,
        N1KV: NEUTRON_N1KV_PLUGIN,
        NSX: NEUTRON_NSX_PLUGIN
    },
}


def remap_plugin(plugin):
    ''' Remaps plugin name for renames/switches in packaging '''
    release = get_os_codename_install_source(config('openstack-origin'))
    if plugin == 'nvp' and release >= 'icehouse':
        plugin = 'nsx'
    elif plugin == 'nsx' and release < 'icehouse':
        plugin = 'nvp'
    return plugin


def core_plugin():
    plugin = remap_plugin(config('plugin'))
    if (get_os_codename_install_source(config('openstack-origin'))
            >= 'icehouse'
            and plugin == OVS):
        return NEUTRON_ML2_PLUGIN
    else:
        return CORE_PLUGIN[networking_name()][plugin]


def neutron_api_settings():
    '''
    Inspects current neutron-plugin-api relation for neutron settings. Return
    defaults if it is not present
    '''
    neutron_settings = {
        'l2_population': False,
        'enable_dvr': False,
        'enable_l3ha': False,
        'overlay_network_type': 'gre',

    }
    for rid in relation_ids('neutron-plugin-api'):
        for unit in related_units(rid):
            rdata = relation_get(rid=rid, unit=unit)
            if 'l2-population' not in rdata:
                continue
            neutron_settings['l2_population'] = \
                bool_from_string(rdata['l2-population'])
            if 'overlay-network-type' in rdata:
                neutron_settings['overlay_network_type'] = \
                    rdata['overlay-network-type']
            if 'enable-dvr' in rdata:
                neutron_settings['enable_dvr'] = \
                    bool_from_string(rdata['enable-dvr'])
            if 'enable-l3ha' in rdata:
                neutron_settings['enable_l3ha'] = \
                    bool_from_string(rdata['enable-l3ha'])
            return neutron_settings
    return neutron_settings


class NetworkServiceContext(OSContextGenerator):
    interfaces = ['quantum-network-service']

    def __call__(self):
        for rid in relation_ids('quantum-network-service'):
            for unit in related_units(rid):
                rdata = relation_get(rid=rid, unit=unit)
                ctxt = {
                    'keystone_host': rdata.get('keystone_host'),
                    'service_port': rdata.get('service_port'),
                    'auth_port': rdata.get('auth_port'),
                    'service_tenant': rdata.get('service_tenant'),
                    'service_username': rdata.get('service_username'),
                    'service_password': rdata.get('service_password'),
                    'quantum_host': rdata.get('quantum_host'),
                    'quantum_port': rdata.get('quantum_port'),
                    'quantum_url': rdata.get('quantum_url'),
                    'region': rdata.get('region'),
                    'service_protocol':
                    rdata.get('service_protocol') or 'http',
                    'auth_protocol':
                    rdata.get('auth_protocol') or 'http',
                }
                if context_complete(ctxt):
                    return ctxt
        return {}


class L3AgentContext(OSContextGenerator):

    def __call__(self):
        api_settings = neutron_api_settings()
        ctxt = {}
        if config('run-internal-router') == 'leader':
            ctxt['handle_internal_only_router'] = eligible_leader(None)

        if config('run-internal-router') == 'all':
            ctxt['handle_internal_only_router'] = True

        if config('run-internal-router') == 'none':
            ctxt['handle_internal_only_router'] = False

        if config('external-network-id'):
            ctxt['ext_net_id'] = config('external-network-id')
        if config('plugin'):
            ctxt['plugin'] = config('plugin')
        if api_settings['enable_dvr']:
            ctxt['agent_mode'] = 'dvr_snat'
        else:
            ctxt['agent_mode'] = 'legacy'
        return ctxt


class NeutronPortContext(OSContextGenerator):

    def _resolve_port(self, config_key):
        if not config(config_key):
            return None
        hwaddr_to_nic = {}
        hwaddr_to_ip = {}
        for nic in list_nics(['eth', 'bond']):
            hwaddr = get_nic_hwaddr(nic)
            hwaddr_to_nic[hwaddr] = nic
            addresses = get_ipv4_addr(nic, fatal=False) + \
                get_ipv6_addr(iface=nic, fatal=False)
            hwaddr_to_ip[hwaddr] = addresses
        mac_regex = re.compile(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', re.I)
        for entry in config(config_key).split():
            entry = entry.strip()
            if re.match(mac_regex, entry):
                if entry in hwaddr_to_nic and len(hwaddr_to_ip[entry]) == 0:
                    # If the nic is part of a bridge then don't use it
                    if is_bridge_member(hwaddr_to_nic[entry]):
                        continue
                    # Entry is a MAC address for a valid interface that doesn't
                    # have an IP address assigned yet.
                    return hwaddr_to_nic[entry]
            else:
                # If the passed entry is not a MAC address, assume it's a valid
                # interface, and that the user put it there on purpose (we can
                # trust it to be the real external network).
                return entry
        return None


class ExternalPortContext(NeutronPortContext):

    def __call__(self):
        port = self._resolve_port('ext-port')
        if port:
            return {"ext_port": port}
        else:
            return None


class DataPortContext(NeutronPortContext):

    def __call__(self):
        port = self._resolve_port('data-port')
        if port:
            return {"data_port": port}
        else:
            return None


class QuantumGatewayContext(OSContextGenerator):

    def __call__(self):
        api_settings = neutron_api_settings()
        ctxt = {
            'shared_secret': get_shared_secret(),
            'local_ip':
            get_address_in_network(config('os-data-network'),
                                   get_host_ip(unit_get('private-address'))),
            'core_plugin': core_plugin(),
            'plugin': config('plugin'),
            'debug': config('debug'),
            'verbose': config('verbose'),
            'instance_mtu': config('instance-mtu'),
            'l2_population': api_settings['l2_population'],
            'enable_dvr': api_settings['enable_dvr'],
            'enable_l3ha': api_settings['enable_l3ha'],
            'overlay_network_type':
            api_settings['overlay_network_type'],
        }
        return ctxt


@cached
def get_host_ip(hostname=None):
    try:
        import dns.resolver
    except ImportError:
        apt_install('python-dnspython', fatal=True)
        import dns.resolver
    hostname = hostname or unit_get('private-address')
    try:
        # Test to see if already an IPv4 address
        socket.inet_aton(hostname)
        return hostname
    except socket.error:
        answers = dns.resolver.query(hostname, 'A')
        if answers:
            return answers[0].address


SHARED_SECRET = "/etc/{}/secret.txt"


def get_shared_secret():
    secret = None
    _path = SHARED_SECRET.format(networking_name())
    if not os.path.exists(_path):
        secret = str(uuid.uuid4())
        with open(_path, 'w') as secret_file:
            secret_file.write(secret)
    else:
        with open(_path, 'r') as secret_file:
            secret = secret_file.read().strip()
    return secret
