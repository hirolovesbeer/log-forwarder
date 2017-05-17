#!/usr/bin/env python

import sys, socket, time, os
from multiprocessing import Process

import yaml

SYSLOG_PORT = 514
NR_LISTENERS = os.cpu_count()

SO_REUSEPORT = 15

BUFSIZE = 1024
DST_HOST = "192.168.11.13"

CONFIG = 'config.yml'

def listener_work(num, dst_hosts, dst_filter_hosts, filter_list, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, SO_REUSEPORT, 1)   # set SO_REUSEPORT
    s.bind(("", port))

    try:
        while True:
            data, addr = s.recvfrom(BUFSIZE)

            for dst in dst_filter_hosts:
                # match filter list
                if len([x for x in filter_list if x == addr[0]]) == 1:
                    continue
                else:
                    s.sendto(data, (dst, port))

            for dst in dst_hosts:
               s.sendto(data, (dst, port))

    except KeyboardInterrupt:
        print ("Crtl+C Pressed. Shutting down.")

def server():
    with open(CONFIG) as f:
        config = yaml.load(f)

    dst_hosts = config['syslog-all']
    dst_filter_hosts = config['syslog-filter']
    filter_list = config['filter-list']

    processes = []
    for i in range(NR_LISTENERS):
        p = Process(target=listener_work, args=(i, dst_hosts, dst_filter_hosts, filter_list, SYSLOG_PORT))
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
