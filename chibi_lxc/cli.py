# -*- coding: utf-8 -*-
import time
import argparse
import sys
from chibi.file import Chibi_path
from chibi.config import basic_config, load as load_config
from chibi_lxc.config import configuration
from chibi_lxc.container import Not_exists_error
from python_hosts import Hosts, HostsEntry
import datetime


def get_ip( container, timeout=60 ):
    start = datetime.datetime.now()
    while ( datetime.datetime.now() - start ).total_seconds() < timeout:
        time.sleep( 3 )
        info = container.info.result
        if 'ip' in info:
            return info.ip
    raise TimeoutError( f"waiting {container.name}" )


def read_hosts():
    hosts_file = configuration.chibi_lxc.hosts
    hosts = Hosts( hosts_file )
    return hosts


def remove_host_if_exists( host ):
    hosts = read_hosts()
    entries = []
    for entry in hosts.entries:
        if host in entry.names:
            continue
        entries.append( entry )
    hosts.entries = entries
    hosts.write()


def init_hosts_file():
    hosts = read_hosts()
    hosts.entries = []
    hosts.add( [
        HostsEntry(
            entry_type='ipv4', address='127.0.0.1',
            names=[ 'localhost' ] ),
        HostsEntry(
            entry_type='ipv6', address='::1',
            names=[ 'localhost' ] ),
    ] )
    hosts.write()


def add_address_to_host( address, host ):
    remove_host_if_exists( host )
    hosts = read_hosts()
    if not hosts.entries:
        init_hosts_file()
        hosts = read_hosts()
    hosts.add( [ HostsEntry(
        entry_type='ipv4', address=address, names=[ host ] ) ] )
    hosts.write()


def main():
    parser = argparse.ArgumentParser(
        "tool for build containers" )
    parser.add_argument(
        "--log_level", dest="log_level", default="INFO",
        help="nivel de log", )

    parser.add_argument(
        "config", type=Chibi_path,
        help="python, yaml o json archivo con los settings" )

    sub_parsers = parser.add_subparsers(
        dest='command', help='sub-command help' )

    parser_list = sub_parsers.add_parser(
        'list', help='list the backups', )

    parser_start = sub_parsers.add_parser(
        'up', help='start the container', )
    parser_start.add_argument(
        "containers", nargs='+', metavar="containers",
        help="contenedores que se iniciaran" )

    parser_start = sub_parsers.add_parser(
        'provision', help='start the container', )
    parser_start.add_argument(
        "containers", nargs='+', metavar="containers",
        help="contenedores que se iniciaran" )

    parser_status = sub_parsers.add_parser(
        'status', help='', )
    parser_status.add_argument(
        "containers", nargs='*', metavar="containers",
        default=configuration.chibi_lxc.containers,
        help="contenedores que se iniciaran" )

    parser_info = sub_parsers.add_parser(
        'info', help='', )
    parser_info.add_argument(
        "containers", nargs='+', metavar="containers",
        help="contenedores que se iniciaran" )

    parser_destroy = sub_parsers.add_parser(
        'destroy', help='destroy the container', )
    parser_destroy.add_argument(
        "containers", nargs='+', metavar="containers",
        help="contenedores que se iniciaran" )

    parser_destroy.add_argument(
        "--force", "-f", action="store_true",
        help="fuerza a deneter el contenedor y lo destruye" )

    parser_stop = sub_parsers.add_parser(
        'stop', help='stop the container', )
    parser_stop.add_argument(
        "containers", nargs='+', metavar="containers",
        help="contenedores que se iniciaran" )

    args = parser.parse_args()
    basic_config( level=args.log_level )
    load_config( args.config )

    if args.command == 'list':
        containers = configuration.chibi_lxc.containers
        for name, container in containers.items():
            print( name, container )

    if args.command == 'up':
        containers = configuration.chibi_lxc.containers
        for container in args.containers:
            container = containers[ container ]
            exists = container.exists
            if not exists:
                container.create()
            container.provision()
            container.start()
            ip = get_ip( container )
            add_address_to_host( ip, container.name )
            if not exists:
                container.provision()
                container.run_scripts()

    if args.command == 'provision':
        containers = configuration.chibi_lxc.containers
        for container in args.containers:
            container = containers[ container ]
            container.provision()
            container.start()
            time.sleep( 10 )
            add_address_to_host( container.info.result.ip, container.name )
            container.provision()
            container.run_scripts()

    if args.command == 'status':
        containers = configuration.chibi_lxc.containers
        for container in args.containers:
            print( container )
            container = containers[ container ]
            try:
                info = container.info.result
            except Not_exists_error:
                print( '\t', 'no exists' )
                continue
            for k, v in info.items():
                print( '\t', k, v )

    if args.command == 'info':
        containers = configuration.chibi_lxc.containers
        for container in args.containers:
            print( container )
            container = containers[ container ]
            for s in container.scripts:
                print( '\t', s )

    if args.command == 'destroy':
        containers = configuration.chibi_lxc.containers
        for container in args.containers:
            container = containers[ container ]
            if args.force and container.info.is_running:
                container.stop()
            container.destroy()

    if args.command == 'stop':
        containers = configuration.chibi_lxc.containers
        for container in args.containers:
            container = containers[ container ]
            container.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
