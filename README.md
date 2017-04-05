# Log Forwarder(as known as Sekiwake)
This software is prototype of syslog/xflow/snmptrap forwarder.

# Concept
- Received syslog/xflow/snmptrap using UDP Socket
- Pure python implement
- Using Hardware NIC acceleration
  - RSS(Recieve Side Scaling)
- Core-scale architecture
  - multiprocessing
  - SO_REUSEPORT
  - irqbalance

# Environment
- CentOS 7.3
- Python 3.5.1(used anaconda packages)

# Dependency softwares
- PyYaml
  - $ conda install yaml
- supervisord(daemonize)
  - $ sudo yum install supervisor

# Benchmark
- TBD
