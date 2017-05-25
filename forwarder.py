#!/usr/bin/env python

import argparse

import sys, socket, time, os
from multiprocessing import Process

import yaml
import ipaddress

PORT = 514
NR_LISTENERS = 1
CORES = 0

SO_REUSEPORT = 15

BUFSIZE = 1024

CONFIG = 'config.yml'

def listener_work(num, config, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, SO_REUSEPORT, 1)   # set SO_REUSEPORT
    s.bind(("", port))

    src_security = ipaddress.ip_network(config['syslog']['src-security'])

    try:
        while True:
            data, addr = s.recvfrom(BUFSIZE)

            # syslog
            if port == config['port']['syslog']:
                # security only
                src_ip = ipaddress.ip_network(dst)

#                if addr[0] in config['syslog']['src-security']:
                if src_ip.compare_networks(src_security) == 1:
                    # src securityからのsyslog
                    for dst in config['syslog']['dst-security-only']:
                        # security-onlyへ飛ばす
                        s.sendto(data, (dst, port))
                else:
                    # mgmt(security以外)からのsyslog
                    for dst in config['syslog']['dst-mgmt-only']:
                        # mgmt-onlyへ飛ばす
                        s.sendto(data, (dst, port))

                # all
                for dst in config['syslog']['dst-all']:
                    s.sendto(data, (dst, port))
            # trap
            elif port == config['port']['trap']:
                for dst in config['trap']['dst-all']:
                    s.sendto(data, (dst, port))
            # xflow
            else:
                for dst in config['xflow']['dst-all']:
                    s.sendto(data, (dst, port))

    except KeyboardInterrupt:
        print ("Crtl+C Pressed. Shutting down.")

def server(args):
    global CONFIG
    global PORT
    global NR_LISTENERS
    global CORES

    if args.c != False:
        CONFIG = args.c

    with open(CONFIG) as f:
        config = yaml.load(f)

    # 指定がなければsyslog転送が起動
    if args.f:
        PORT = config['port']['xflow'] 
        NR_LISTENERS = config['process']['xflow']
        CORES = config['core']['xflow']
    elif args.t:
        PORT = config['port']['trap'] 
        NR_LISTENERS = config['process']['trap']
        CORES = config['core']['trap']
    else:
        PORT = config['port']['syslog'] 
        NR_LISTENERS = config['process']['syslog']
        CORES = config['core']['syslog']

    processes = []
    if args.f:
        # xflowはそれぞれ1つずつのポートでプロセスをあげる
        ports = PORT.split(',')

        for port in ports:
            for i in range(NR_LISTENERS):
                p = Process(target=listener_work, args=(i, config, int(port)))
                p.start()
                #os.system("taskset -p -c %d %d" % ((i % NR_LISTENERS), p.pid))
                os.system("taskset -p -c %s %d" % (CORES, p.pid))
                processes.append(p)

    else:
        for i in range(NR_LISTENERS):
            p = Process(target=listener_work, args=(i, config, PORT))
            p.start()
            # os.system("taskset -p -c %d %d" % ((i % NR_LISTENERS), p.pid))
            os.system("taskset -p -c %s %d" % (CORES, p.pid))
            processes.append(p)

    for p in processes:
        p.join()

def main(args):
    try:
        server(args)
    except(IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print ("Crtl+C Pressed. Shutting down.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", type=str, default=False,
                        help="config file")
    parser.add_argument("-s",
                        help="syslog", action="store_true")
    parser.add_argument("-f",
                        help="xflow", action="store_true")
    parser.add_argument("-t",
                        help="trap", action="store_true")
    parser.parse_args()

    args = parser.parse_args()

    main(args)
