# -*- coding: utf-8 -*-

try:
    from oslo.config import cfg
except ImportError:
    from oslo_config import cfg

import novaclient.exceptions as novaclientexceptions
from syseleven.cloudutilslibs.openstackclients import (get_heat_client,
                                                    get_neutron_client,
                                                    get_nova_client)
from syseleven.cloudutilslibs.log import start_logging
from syseleven.cloudutilslibs.utils import get_floating_ip_from_heat_nova_neutron

from syseleven.cloudutils.show_heat_floating_ips.opts import init_params


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
