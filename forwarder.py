#!/usr/bin/env python

import sys, socket, time, os
from multiprocessing import Process

import yaml

SYSLOG_PORT = 514
NR_LISTENERS = os.cpu_count()

SO_REUSEPORT = 15

BUFSIZE = 1024

CONFIG = 'config.yml'

def listener_work(num, config, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, SO_REUSEPORT, 1)   # set SO_REUSEPORT
    s.bind(("", port))

    try:
        while True:
            data, addr = s.recvfrom(BUFSIZE)

            # security only
            if addr[0] in config['syslog']['src-security']:
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

    except KeyboardInterrupt:
        print ("Crtl+C Pressed. Shutting down.")

def server():
    with open(CONFIG) as f:
        config = yaml.load(f)

    processes = []
    for i in range(NR_LISTENERS):
        p = Process(target=listener_work, args=(i, config, SYSLOG_PORT))
        p.start()
        os.system("taskset -p -c %d %d" % ((i % os.cpu_count()), p.pid))
        processes.append(p)

    for p in processes:
        p.join()

def main():
    try:
        server()
    except(IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print ("Crtl+C Pressed. Shutting down.")

if __name__ == '__main__':
    main()
