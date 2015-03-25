# -*- coding: utf-8 -*-

from oslo.config import cfg

import novaclient.exceptions as novaclientexceptions
from syseleven.cloudutils.openstackclients import (get_heat_client,
                                                    get_neutron_client,
                                                    get_nova_client)

from syseleven.cloudutils.log import start_logging
from syseleven.cloudutils.show_heat_floating_ips.opts import init_params
from syseleven.cloudutils.utils import get_floating_ip_from_heat_nova_neutron


def main():
    init_params()
    global LOG
    LOG = start_logging()


    heatclient = get_heat_client()
    neutronclient = get_neutron_client()
    novaclient = get_nova_client()

    fields = {'stack_id': cfg.CONF.stack}
    stack = heatclient.stacks.get(**fields)
    heatstack = get_floating_ip_from_heat_nova_neutron(stack, heatclient, neutronclient, novaclient)

    for server, floatingip in heatstack:
        print "%s %s %s" % (server.name, floatingip, server.id)
if __name__ == 'main':
    main()
