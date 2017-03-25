#!/usr/bin/python
import yaml
import json
import argparse
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ETtree
import os
import sys

import factory
import splunk
import parser


def dump(data):
    return json.dumps(data, indent=2)


def pretty_xml(data):
    """
    Return a pretty-printed XML string for the xml data.
    """
    rough_string = ETtree.tostring(data, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def is_valid_xml(data):
    try:
        ETtree.fromstring(data, parser=ETtree.XMLParser(encoding='utf-8'))
        return True
    except ETtree.ParseError as e:
        print e
        return False


def open_read_yaml(path):
    with open(path) as df:
        return yaml.load(df)


def create_argument_parser():
    p = argparse.ArgumentParser(description='Tool to generate and publish dashboards to Splunk')
    subparsers = p.add_subparsers(help='commands')

    # Generate mode parser
    gen_parser = subparsers.add_parser('generate')
    gen_parser.add_argument('path', metavar='PATH_TO_YAML_DASHBOARD',
                            type=str, nargs=1,
                            help='Path to the dashboard yaml definition')

    gen_parser.set_defaults(mode='gen')

    # Publish mode parser
    pub_parser = subparsers.add_parser('publish')
    pub_parser.add_argument('-S', '--splunk-settings',
                            type=str, default=os.path.expanduser('~/.splunk'),
                            help='Path to your Splunk settings. By default, ~/.splunk')

    pub_parser.add_argument('-a', '--app',
                            type=str,
                            help='Splunk App where the dashboard should be published')

    pub_parser.add_argument('path',
                            metavar='PATH_TO_XML_DASHBOARD',
                            type=str, nargs=1,
                            help='Path to the dashboard xml definition')

    pub_parser.set_defaults(mode='pub')
    return p


def generate_mode(options):
    data = open_read_yaml(options.path[0])

    print pretty_xml(
        factory.create(
            parser.parse(data)))

    return 0


def publish_mode(options):
    path = options.path[0]
    with open(path) as fp:
        data = fp.read()

    if not is_valid_xml(data):
        raise ValueError('not valid xml input')

    print "dashboard is valid xml"
    print "warning, the xml file is not validated against splunk dashboard schema"

    settings = open_read_yaml(options.splunk_settings)['settings']
    user = settings["username"]
    password = settings["password"]
    api = settings["api"]
    port = settings.get("port", 8089)

    client = splunk.Client(splunk.ServerInfo(api, port),
                           splunk.AuthenticationInfo(user, password))

    dashboard = os.path.splitext(
        os.path.basename(path))[0]

    print "checking dashboard status"
    if client.dashboards().exists(options.app, dashboard):
        print "will update dashboard '{}' in App '{}'".format(dashboard, options.app)
        client.dashboards().update(
            options.app,
            dashboard,
            data)
    else:
        print "will create a new dashboard '{}' in App '{}'".format(dashboard, options.app)
        client.dashboards().create(
            options.app,
            dashboard,
            data)

    print "dashboard published successfully"
    return 0


def modes():
    return {
        'gen': generate_mode,
        'pub': publish_mode
    }


def main():
    p = create_argument_parser()
    options = p.parse_args()

    handler = modes()[options.mode]
    sys.exit(handler(options))

if __name__ == "__main__":
    main()
