#!/usr/bin/env python3
"""
Birzeit University - Department of Electrical and Computer Engineering
Advanced Computer Networks (ENCS5321) - Assignment #1
Task 3: Redundant Diamond Topology for Link Failure Recovery (task3_recovery.py)

Author: Motaz Altell

Description:
    Creates a diamond-shaped OpenFlow 1.3 topology with four switches (s1..s4)
    and two hosts (h1, h2) connected to a remote Ryu SDN controller at
    127.0.0.1:6653. Two disjoint paths connect h1 (on s1) to h2 (on s4):
      - Primary path: s1 (port 2) <-> s2 <-> s4 (port 2)
      - Backup path:  s1 (port 3) <-> s3 <-> s4 (port 3)
    Deterministic link addition order ensures predictable switch port numbering
    for the proactive flow rules installed by task3_controller.py.
"""

from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel


def run():
    """Instantiate the redundant OpenFlow 1.3 diamond topology and launch CLI."""
    # Disable default controller and enable deterministic MAC assignment (autoSetMacs=True)
    net = Mininet(
        controller=None,
        switch=OVSSwitch,
        autoSetMacs=True
    )

    # Add two end hosts in the 10.0.0.0/24 subnet
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')

    # Connect to the external Ryu SDN controller listening on TCP port 6653
    net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6653
    )

    # Add four Open vSwitch instances configured to speak OpenFlow 1.3
    s1 = net.addSwitch('s1', protocols='OpenFlow13')
    s2 = net.addSwitch('s2', protocols='OpenFlow13')
    s3 = net.addSwitch('s3', protocols='OpenFlow13')
    s4 = net.addSwitch('s4', protocols='OpenFlow13')

    # Host connections (assigned port 1 on edge switches s1 and s4)
    net.addLink(h1, s1)
    net.addLink(h2, s4)

    # Primary path: s1 (port 2) -> s2 (port 1, port 2) -> s4 (port 2)
    net.addLink(s1, s2)
    net.addLink(s2, s4)

    # Backup path: s1 (port 3) -> s3 (port 1, port 2) -> s4 (port 3)
    net.addLink(s1, s3)
    net.addLink(s3, s4)

    # Start switches, connect them to Ryu c0, and configure host interfaces
    net.start()

    print("*** Primary: s1 -> s2 -> s4")
    print("*** Backup:  s1 -> s3 -> s4")

    # Launch interactive CLI to execute `link s1 s2 down`, ping tests, and ovs-ofctl dumps
    CLI(net)
    # Stop network and clean up interfaces upon CLI exit
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
