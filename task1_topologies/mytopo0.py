#!/usr/bin/python
"""
Birzeit University - Department of Electrical and Computer Engineering
Advanced Computer Networks (ENCS5321) - Assignment #1
Task 1.3: Custom Network Topology in Python (mytopo0.py)

Author: Motaz Altell

Description:
    Defines a custom linear two-switch, two-host Mininet topology by subclassing
    mininet.topo.Topo. Hosts are assigned static IPv4 addresses and MAC addresses,
    and are registered in the `topos` dictionary under the key 'mytopo' so the
    topology can be invoked via:
        sudo mn --custom mytopo0.py --topo mytopo --link tc
"""

from mininet.topo import Topo


class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."
        # Initialize the base Mininet Topo class before adding nodes and links
        Topo.__init__( self )

        # Add hosts and switches with static IP and MAC addresses
        # leftHost (h1) connects to leftSwitch (s3)
        leftHost = self.addHost( 'h1', ip='192.168.1.100', mac='00:00:00:00:00:11' )
        # rightHost (h2) connects to rightSwitch (s4)
        rightHost = self.addHost( 'h2', ip='192.168.1.101', mac='00:00:00:00:00:22' )

        # Create two virtual Open vSwitch instances (s3 and s4)
        leftSwitch = self.addSwitch( 's3' )
        rightSwitch = self.addSwitch( 's4' )

        # Add bidirectional links connecting hosts to switches and switches to each other
        # Path formed: h1 (192.168.1.100) <--> s3 <--> s4 <--> h2 (192.168.1.101)
        self.addLink( leftHost, leftSwitch )
        self.addLink( leftSwitch, rightSwitch )
        self.addLink( rightSwitch, rightHost )


# Expose the custom topology to the Mininet CLI `--topo mytopo` option
topos = { 'mytopo': ( lambda: MyTopo() ) }
