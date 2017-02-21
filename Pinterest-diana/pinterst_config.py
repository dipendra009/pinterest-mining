#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################################
# Author: Diana Palsetia
# Usuage: python config.py
# Date: 2016-04-23
################################################################################
from configobj import ConfigObj

config = ConfigObj()
config.filename = "pinterest.cfg"


config['firefox_path'] = '/usr/lib64/firefox/firefox-bin'


pin1 = {'email' : 'alokchoudhary01@yahoo.com',
        'password' : 'Techl469'
}
config['pin1'] = pin1

config.write()
