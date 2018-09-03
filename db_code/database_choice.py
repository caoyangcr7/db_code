# -*- coding:utf8 -*-

import os
import ConfigParser
import sys

def configParse(database):
    # choose diffrent databases  for web or for PC
    cf  = ConfigParser.SafeConfigParser()
    if database == "DaZhu":
        config_path = 'dazhu_basic_information.conf'
        # cf = ConfigParser.SafeConfigParser()
        file_path = os.path.dirname(__file__) + '/config/' + config_path
        # print file_path
        cf.read(file_path)
        config = {
            'host': cf.get("DBInstance", "host"),
            'user': cf.get("DBInstance", "user"),
            'passwd': cf.get("DBInstance", "passwd"),
            'db': cf.get("DBInstance", "db"),
            'charset': cf.get("DBInstance", "charset")
        }
    if database == "exo":
        config_path = "bfr_exo_information.conf"
        # cf = ConfigParser.SafeConfigParser()
        file_path = os.path.dirname(__file__) + '/config/' + config_path
        # print file_path
        cf.read(file_path)
        config = {
            'host': cf.get("DBInstance", "host"),
            'user': cf.get("DBInstance", "user"),
            'passwd': cf.get("DBInstance", "passwd"),
            'db': cf.get("DBInstance", "db"),
            'charset': cf.get("DBInstance", "charset")
        }
    if database == 'rds':
        config_path = "cloud1_bfr_test.conf"
        file_path = os.path.dirname(__file__) + '/config/' +config_path
        cf.read(file_path)
        config = {
            'host': cf.get("DBInstance", "host"),
            'user': cf.get("DBInstance", "user"),
            'passwd': cf.get("DBInstance", "passwd"),
            'db': cf.get("DBInstance", "db"),
            'charset': cf.get("DBInstance", "charset")
        }

    # print config
    return config


