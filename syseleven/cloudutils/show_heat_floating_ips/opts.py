# -*- coding: utf-8 -*-

import os
import sys
import ConfigParser

from oslo.config import cfg


def init_params():
    """ this functions load all parameter either from
        command-line OR config-file/config-dir """

    params = [
        cfg.StrOpt('stack',
                    positional=True,
                    help='Name of the stack'
                    ),
        cfg.BoolOpt('debug',
                    short='d',
                    help='Enable debug'
                    ),
    ]

    cfg.CONF.register_cli_opts(params)
    cfg.CONF.register_opts(params)

    cfg.CONF(sys.argv[1:],
            project='show_heat_floating_ips',
            prog='show_heat_floating_ips',
            )
