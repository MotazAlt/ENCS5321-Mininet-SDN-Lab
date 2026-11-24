#!/usr/bin/env python3
"""
Birzeit University - Department of Electrical and Computer Engineering
Advanced Computer Networks (ENCS5321) - Assignment #1
Task 2: Network Congestion and Queue Management Topology (task2.py)

Author: Motaz Altell

Description:
    Builds a four-host, two-switch Mininet network with a shared 10 Mb/s
    bottleneck link between switches s1 and s2 using Linux Traffic Control (TCLink).
    Hosts h1, h2, and h3 connect to switch s1 via 100 Mb/s access links, while
    receiver host h4 connects to switch s2 via a 100 Mb/s access link.
    Because all s1-to-s2 traffic traverses interface s1-eth4 (rate-limited to
    10 Mb/s via HTB), simultaneous TCP (h1->h4), UDP (h2->h4), and ICMP ping
    (h1->h4) flows contend at s1-eth4, enabling direct comparison of FIFO
    (pfifo) and RED (Random Early Detection) queue management disciplines.
"""

from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel


def run():
    """Construct, start, and enter CLI for the Task 2 bottleneck topology."""
    # Instantiate Mininet with standalone OVS switches (no remote controller)
    # and TCLink to enforce per-link bandwidth limits via Linux tc
    net = Mininet(
        controller=None,
        switch=OVSSwitch,
        link=TCLink
    )

    # Add hosts: h1 (TCP sender & ping), h2 (UDP sender), h3 (extra sender/node), h4 (receiver)
    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    h3 = net.addHost('h3')
    h4 = net.addHost('h4')

    # Add switches in standalone Layer-2 learning mode so traffic forwards automatically
    s1 = net.addSwitch('s1', failMode='standalone')
    s2 = net.addSwitch('s2', failMode='standalone')

    # Host access links: high capacity (100 Mb/s) so hosts are not the bottleneck
    # Interface order on s1: s1-eth1->h1, s1-eth2->h2, s1-eth3->h3
    net.addLink(h1, s1, bw=100)
    net.addLink(h2, s1, bw=100)
    net.addLink(h3, s1, bw=100)
    net.addLink(h4, s2, bw=100)

    # Shared bottleneck link between s1 (s1-eth4) and s2 (s2-eth2): 10 Mb/s
    net.addLink(s1, s2, bw=10)

    # Boot the virtual network and configure host interfaces
    net.start()

    print("Network started")
    # Enter interactive Mininet CLI to run tc qdisc commands, iperf, and ping tests
    CLI(net)

    # Cleanly tear down virtual links, namespaces, and OVS bridges on exit
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
