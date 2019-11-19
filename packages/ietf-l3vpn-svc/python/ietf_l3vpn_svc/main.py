# -*- mode: python90; python-indent: 4 -*-
import ncs
from ncs.application import Service

from ietf_l3vpn_svc.network_helper import (get_ip_address, prefix_to_net_mask,
                                           get_next_ipv4_address,
                                           get_net_mask, get_wildcard_mask)
from resource_manager.id_allocator import id_request, id_read
from resource_manager.ipaddress_allocator import net_request, net_read

PE_ASN = 100
CE_ASN = 65000

VRF_ID_POOL_NAME = 'vrf-id-pool'
IP_ADDRESS_POOL_NAME = 'topology-connections-ip-address-pool'
VLAN_ID_POOL_NAME = 'topology-connections-vlan-id-pool'


# ---------------------------------
# SERVICE CALLBACK OBJECT/FUNCTIONS
# ---------------------------------

class ServiceCallbacks(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        # The create() callback is invoked inside NCS FASTMAP and must
        # always be registered.
        self.log.debug("Service create ", service.site_id)

        for site_network_access in service.site_network_accesses.\
                                   site_network_access:
            ce_name = site_network_access.device_reference
            conn = find_connection(root, ce_name)
            if conn:
                self.configure_site(root, tctx.username, service,
                                    site_network_access,
                                    get_connected_endpoint(conn, ce_name),
                                    get_my_endpoint(conn, ce_name))


    def configure_site(self, root, username, service,
                       site_network_access, pe_endpoint, ce_endpoint):

        self.log.info('Configuring site-network-access %s'
                      % site_network_access.site_network_access_id)

        pe_name = pe_endpoint.device
        ce_name = ce_endpoint.device
        vpn_name = site_network_access.vpn_attachment.vpn_id

        [pe_vrf_id, ip_network, vlan_id] = allocate_resources(
            service, root, username, vpn_name, pe_name, ce_name)

        if not (pe_vrf_id and ip_network and vlan_id):
            self.log.info('Resources not ready for %s'
                          % site_network_access.site_network_access_id)
            return

        if not site_network_access.deploy:
            self.log.info('Deploy flag not set')
            return

        link_pe_address = get_next_ipv4_address(get_ip_address(ip_network))
        link_ce_address = get_next_ipv4_address(link_pe_address)

        local_prefix_length = site_network_access.ip_connection.\
                              ipv4.addresses.prefix_length or 32

        tv = ncs.template.Variables()
        tv.add('PE', pe_name)
        tv.add('CE', ce_name)
        tv.add('VLAN_ID', vlan_id)
        tv.add('LINK_PE_ADR', link_pe_address)
        tv.add('LINK_CE_ADR', link_ce_address)
        tv.add('LINK_MASK', get_net_mask(ip_network))
        tv.add('LOCAL_MASK', prefix_to_net_mask(local_prefix_length))
        if pe_endpoint.interface.startswith('GigabitEthernet'):
            tv.add('PE_INT_NAME', 'GigabitEthernet')
            tv.add('PE_INT_NUMBER', pe_endpoint.interface[15:])
        if ce_endpoint.interface.startswith('GigabitEthernet'):
            tv.add('CE_INT_NAME', 'GigabitEthernet')
            tv.add('CE_INT_NUMBER', ce_endpoint.interface[15:])
        tmpl = ncs.template.Template(site_network_access)
        tv.add('PE_ASN', PE_ASN)
        tv.add('CE_ASN', CE_ASN)
        tv.add('ROUTE_DISTINGUISHER', '%d:%d' % (PE_ASN, pe_vrf_id))
        tv.add('ROUTE_TARGET', '%d:%d' % (PE_ASN, pe_vrf_id))
        tmpl.apply('l3vpn-ntw-site-rfs', tv)

        apply_qos_class_rules(site_network_access)
        self.log.info('Finished site-network-access %s')


def apply_qos_class_rules(site_network_access):
    qv = ncs.template.Variables()
    qv.add('SITE_ID', site_network_access.site_network_access_id)
    for qos_class_rule in site_network_access.service.qos.\
                          qos_classification_policy.rule:
        match = qos_class_rule.match_flow
        if match:
            if match.ipv4_src_prefix:
                qv.add('SOURCE_IP_ADDRESS',
                       get_ip_address(match.ipv4_src_prefix))
                qv.add('SOURCE_WILDCARD_MASK',
                       get_wildcard_mask(match.ipv4_src_prefix))
            else:
                qv.add('SOURCE_IP_ADDRESS', 'any')
                qv.add('SOURCE_WILDCARD_MASK', '')

            if match.ipv4_dst_prefix:
                qv.add('DEST_IP_ADDRESS',
                       get_ip_address(match.ipv4_dst_prefix))
                qv.add('DEST_WILDCARD_MASK',
                       get_wildcard_mask(match.ipv4_dst_prefix))
            else:
                qv.add('DEST_IP_ADDRESS', 'any')
                qv.add('DEST_WILDCARD_MASK', '')

            q_tmpl = ncs.template.Template(qos_class_rule)
            q_tmpl.apply('l3vpn-ntw-qos-rule', qv)

def allocate_resources(service, root, username, vpn_name, pe_name, ce_name):
    conn_name = '%s-%s' % (ce_name, pe_name)
    xpath = "/l3vpn-svc:l3vpn-svc/sites/site[site-id='%s']" % service.site_id

    id_request(service, xpath, username, VRF_ID_POOL_NAME, vpn_name, False)
    net_request(service, xpath, username, IP_ADDRESS_POOL_NAME, conn_name, 30)
    id_request(service, xpath, username, VLAN_ID_POOL_NAME, conn_name, False)

    return [id_read(username, root, VRF_ID_POOL_NAME, vpn_name),
            net_read(username, root, IP_ADDRESS_POOL_NAME, conn_name),
            id_read(username, root, VLAN_ID_POOL_NAME, conn_name)]

def find_connection(root, ce_name):
    return next((conn for conn in root.l3vpn_ntw__topology.connection
                 if (conn.endpoint_1.device == ce_name or
                     conn.endpoint_2.device == ce_name)), None)

def get_connected_endpoint(conn, ce_name):
    if conn.endpoint_1.device == ce_name:
        return conn.endpoint_2
    return conn.endpoint_1

def get_my_endpoint(conn, ce_name):
    if conn.endpoint_1.device == ce_name:
        return conn.endpoint_1
    return conn.endpoint_2


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS
# ---------------------------------------------

class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us.
        # It's a normal logging.getLogger() object.
        self.log.info('Worker RUNNING')
        # Create the Service callback object/functions.
        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        self.register_service('ietf-l3vpn-site', ServiceCallbacks)
        # When we registered service, the Application class took care of
        # creating a daemon related to the servicepoint.
        # When this setup method is finished all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.
        self.log.info('Worker FINISHED')
