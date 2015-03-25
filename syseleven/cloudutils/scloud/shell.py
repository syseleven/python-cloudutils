# -*- coding: utf-8 -*-

import datetime
import time
import os
import json
import StringIO

from oslo.config import cfg

from heatclient.common import utils as heatutils
from heatclient.common import template_utils

from novaclient import utils as novautils

from heatclient.exc import (CommandError,
                            HTTPInternalServerError,
                            HTTPNotFound,
                            HTTPBadRequest)

from neutronclient.common.exceptions import NeutronClientException

from sys11.cloudutilslibs.log import start_logging
from sys11.cloudutilslibs.openstackclients import (get_heat_client,
                                                    get_neutron_client,
                                                    get_nova_client)
from sys11.cloudutilslibs.utils import (dict_merge,
                                        get_floating_ip_from_heat_nova_neutron)
from syseleven.cloudutils.scloud.opts import (init_params,
                                            load_additional_config_setion)


def really_delete_stack(client, stackname):
    fields = {'stack_id': stackname}
    while True:
        time.sleep(1)
        try:
            stack = client.stacks.get(**fields)
        except HTTPNotFound:
            break

        if stack.stack_status == 'DELETE_IN_PROGRESS':
            continue
        else:
            try:
                stack.delete()
            except HTTPNotFound:
                break

        stack = client.stacks.get(**fields)
        print("%s - %s (%s)" %(stackname, stack.stack_status, stack.stack_status_reason))

def get_template():

    # This check should eventually be refactored in a config validator
    if not cfg.CONF.heattemplatebasepath:
        print("heattemplatebasepath is not set, either set it via --heattemplatebasepath or check %s" % ', '.join(cfg.CONF.config_file or cfg.CONF.default_config_files))
        return None

    if not os.path.exists(os.path.expanduser(cfg.CONF.heattemplate)):
        # try using with base path
        template_path = os.path.join(os.path.expanduser(cfg.CONF.heattemplatebasepath), os.path.expanduser(cfg.CONF.heattemplate))

        if os.path.exists(template_path):
            cfg.CONF.heattemplate = template_path
        else:
            print("No such heattemplate-file: %s" % template_path)
            return None

    try:
        tpl_files, template = template_utils.get_template_contents(
                              template_file = os.path.expanduser(cfg.CONF.heattemplate))
    except CommandError as e:
        print(e.message)
        return None

    return template

def validate_template(client, template):
    fields = {
        'template': template,
        #'files': dict(list(tpl_files.items()) + list(env_files.items())),
        #'environment': env
    }

    try:
        validation = client.stacks.validate(**fields)
    except HTTPInternalServerError as e:
        print("Validation of %s failed:" % (cfg.CONF.heattemplate))
        print(e.error['error']['message'])
        return False

    return True
    #import json
    #json.dumps(validation, indent=2, ensure_ascii=False))

def create_stack(client, template, parameters):

    fields = {
        'stack_name': cfg.CONF.stackname,
        #'disable_rollback': not(args.enable_rollback),
        'parameters': parameters,
        'template': template,
        #'files': dict(list(tpl_files.items()) + list(env_files.items())),
        #'environment': env
    }
    timeout = cfg.CONF.createtimeout
    fields['timeout_mins'] = timeout

    try:
        client.stacks.create(**fields)
    except HTTPBadRequest as e:
        print("Error while creating heat stack (%s may contain errors):\n%s" % (cfg.CONF.config_file, e.error['error']['message']))
        return False

    return True


def denormalize_heat_parameters(parameters):
    for key in parameters:
        if key in cfg.CONF.heatparamsfromfiles and len(parameters[key]) != 0:
            try:
                parameters[key] = ''.join(open(os.path.expanduser(parameters[key]), 'r').readlines())
            except IOError as e:
                print("Couldn't read parameter %s from file %s: %s\n" % (key, parameters[key], e.strerror))
                raise
            except:
                parameters[key] = None

    return parameters

def get_console_log(novaclient, server, length=100):
    """ get console-log from server and return last 10 entries """
    server = novautils.find_resource(novaclient.servers, server)
    data = server.get_console_output(length=length)
    return data

def get_phase_from_server(novaclient, server):
    """ try parsing phases from console-log which should
        return 'STAGE $json_string' and return dict
    """
    def parse_phase(phase):

        try:
            ret = json.loads(phase.replace('STAGE', ''))
        except:
            ret = {'state': 'error while getting phase (%s)' % phase}
        return ret


    console_log = get_console_log(novaclient, server.id)
    s = StringIO.StringIO(console_log)
    ret = []
    for line in s:
        if line.startswith('STAGE'):
            ret.append(line.strip('\n'))
            #print("%s - %s" % (server.name, line))

    # return latest phase
    if ret:
        return parse_phase(ret[-1])
    else:
        return {'state': 'n/a'}

def watch_stack(heatclient, neutronclient, novaclient):
    fields = {'stack_id': cfg.CONF.stackname}
    while True:

        try:
            stack = heatclient.stacks.get(**fields)
        except HTTPNotFound as e:
            print(e.error['error']['message'])
            return False

        try:
            heatstack = get_floating_ip_from_heat_nova_neutron(stack, heatclient, neutronclient, novaclient)
        except NeutronClientException:
            pass

        mydate = datetime.datetime.now()
        server_results = []
        final_stage_all = {}
        for server, floatingip in heatstack:
            if stack.stack_status == 'CREATE_COMPLETE':
                # get bootstrapping phase from console-log and add to output
                phase = get_phase_from_server(novaclient, server)

                if 'command' and 'state' and 'script' in phase.keys():
                    # check if final_stage from $stack.conf is reached
                    if phase['state'] == 'finished' and phase['command'] == 'stage_end' and phase['script'] == cfg.CONF.final_stage:
                        final_stage_all[server.id]=True
                        phase_ = 'script bootstrapping complete'
                    else:
                        phase_ = "%(command)s %(state)s [%(script)s]" % (phase)
                        final_stage_all[server.id]=False
                else:
                    phase_ = phase['state']
                server_results.append("%s %s (%s)" % (server.name, floatingip, phase_))
            else:
                server_results.append("%s %s" % (server.name, floatingip))

        os.system('clear')
        print("%s - %s - %s (%s)\n\n" %(mydate.strftime('%Y-%m-%d %H:%M:%S'), stack.stack_name, stack.stack_status, stack.stack_status_reason))
        for server_result in server_results:
            print(server_result)

        # return if all server have reached final_stage
        if len(final_stage_all) > 0 and False not in final_stage_all.values():
            return None
        time.sleep(2)

def get_first_external_net(neutronclient):
    """Returns first external network"""
    for net in neutronclient.list_networks()['networks']:
        if net['router:external']:
            return net['id']
    return None

def main():
    init_params()
    global LOG
    LOG = start_logging()

    heat_params = load_additional_config_setion('heat_params')

    # Use deploy key from DEFAULT section if not given in heat_params section
    # not needed anymore? --config-file must contain all configs anyway so configparser will parse them with the section
    #if 'deploy_key' not in heat_params:
    #    heat_params['deploy_key'] = cfg.CONF.deploy_key

    # Merge CLI parameters like -P key_name=$foo with config.ini
    # CLI params have priority
    heat_params = dict_merge(heat_params, heatutils.format_parameters(cfg.CONF.heatparams))

    try:
        heat_params = denormalize_heat_parameters(heat_params)
    except IOError as e:
        exit(1)

    neutronclient = get_neutron_client()
    if 'public_net_id' in heat_params\
            and heat_params['public_net_id'] == 'auto':
        public_net_id = get_first_external_net(neutronclient)
        if not public_net_id:
            print('Unable to automatically find external net. Specify a '
                  'public_net_id.')
            exit(1)
        heat_params['public_net_id'] = public_net_id

    heatclient = get_heat_client()
    really_delete_stack(heatclient, cfg.CONF.stackname)

    template = get_template()
    if not template:
        exit(1)
    if not validate_template(heatclient, template):
        exit(1)
    if not create_stack(heatclient, template, heat_params):
        exit(1)

    novaclient = get_nova_client()
    try:
        watch_stack(heatclient, neutronclient, novaclient)
    except KeyboardInterrupt:
        pass

if __name__ == 'main':
    main()
