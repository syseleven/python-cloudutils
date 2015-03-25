# -*- coding: utf-8 -*-

import os
import sys
import ConfigParser

from oslo.config import cfg


def init_params():
    """ this functions load all parameter either from
        command-line OR config-file/config-dir """

    params = [
        cfg.StrOpt('stackname',
                   short='n',
                   default='defaultstackname',
                   help='Name for the heat stack.'),
        cfg.StrOpt('heattemplate',
                   short='f',
                   default=None,
                   help='Path to heat template'),
        cfg.StrOpt('heattemplatebasepath',
                   short='b',
                   default=None,
                   help='Path to heat templates'),
        cfg.StrOpt('deploy_key',
                   default=None,
                   help='Path to deploy_key'),
        cfg.IntOpt('createtimeout',
                   default=1,
                   help='Value for heat stack-create timeout'),
        cfg.StrOpt('final_stage',
                   default=None,
                   help='Value for last boostrapping phase'),
        cfg.MultiStrOpt('heatparams',
                   short='P',
                   default=None,
                   help='Pass heat params with -P key=value'),
        cfg.ListOpt('heatparamsfromfiles',
                   default=['repos_yaml', 'deploy_key'],
                   help='For given parameters read file content (e.g. deploy_key=/root/.ssh/id_rsa will be substituted by actual content of file'),
        cfg.BoolOpt('debug',
                    short='d',
                    help='Enable debug'
                    ),
    ]


    cfg.CONF.register_cli_opts(params)
    cfg.CONF.register_opts(params)

    #additional_heat_params = cfg.OptGroup(name='additional_heat_params',
    #                                    title='additional_heat_params')
    #cfg.CONF.register_group(additional_heat_params)
    #cfg.CONF.import_group(additional_heat_params, 'syseleven.cloudutils.scloud.opts')



    default_cfg_file = os.path.expanduser('~/.scloud.conf')
    if not os.path.isfile(os.path.expanduser('~/.scloud.conf')):
        print('No such file: ~/.scloud.conf')
        exit(1)


    cfg.CONF(sys.argv[1:],
            project='scloud',
            prog='scloud',
            default_config_files=[default_cfg_file])


    if not cfg.CONF.heattemplate:
        print('Please specify a heat template. Either via parameter or config file.')
        exit(1)



def configsectionmap(config, section):
    """ convert ConfigParser options object to dict 
        it also skips [DEFAULT] values """
    dict1 = {}
    defaults = dict(config.defaults())
    try:
        options = config.options(section)
    except ConfigParser.NoSectionError:
        return {}
    for option in options:
        try:
            if option in defaults:
                continue
            dict1[option] = config.get(section, option)
        except:
            dict1[option] = None
    return dict1

def load_additional_config_setion(section):
    """ return dict of ini file section from config-file """
    config = ConfigParser.ConfigParser()
    for configfile in cfg.CONF.config_file:
        config.read(os.path.expanduser(configfile))

    sdict = configsectionmap(config, section)
    return sdict
