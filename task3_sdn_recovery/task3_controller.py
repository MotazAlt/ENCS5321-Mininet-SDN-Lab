#!/usr/bin/env python3
"""
Birzeit University - Department of Electrical and Computer Engineering
Advanced Computer Networks (ENCS5321) - Assignment #1
Task 3: Ryu OpenFlow 1.3 Link Failure Detection & Recovery Controller (task3_controller.py)

Author: Motaz Altell

Description:
    Implements a proactive OpenFlow 1.3 SDN controller application (`RecoveryController`)
    using the Ryu framework. Once all four switches (s1..s4) connect via
    EventOFPSwitchFeatures, the controller installs bidirectional port-forwarding rules
    along the primary path (s1 -> s2 -> s4). It continuously listens for OpenFlow
    EventOFPPortStatus notifications; if primary interface s1-eth2 (dpid=1, port=2)
    transitions to a link-down state, the controller immediately clears existing rules,
    installs the backup path (s1 -> s3 -> s4), and logs its internal processing latency.
"""

import time

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (
    CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
)
from ryu.ofproto import ofproto_v1_3


class RecoveryController(app_manager.RyuApp):
    """Ryu SDN application providing proactive path setup and fast port-status failover."""

    # Enforce OpenFlow 1.3 across all managed switches
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        """Initialize datapath registry and default active path state."""
        super().__init__(*args, **kwargs)
        # Map switch DPID (1..4) -> Datapath object
        self.datapaths = {}
        # Start on the primary route (s1 -> s2 -> s4)
        self.active_path = 'primary'

    # Install one forwarding rule
    def add_flow(self, dp, in_port, out_port):
        """Send an OFPFlowMod message matching `in_port` and forwarding to `out_port`."""
        parser = dp.ofproto_parser
        ofp = dp.ofproto

        # Match packets arriving on the specified switch ingress port
        match = parser.OFPMatch(in_port=in_port)
        actions = [parser.OFPActionOutput(out_port)]
        instructions = [
            parser.OFPInstructionActions(
                ofp.OFPIT_APPLY_ACTIONS, actions
            )
        ]

        # Push flow rule with priority 100 into flow table 0
        dp.send_msg(parser.OFPFlowMod(
            datapath=dp,
            priority=100,
            match=match,
            instructions=instructions
        ))

    # Remove previous forwarding rules
    def clear_flows(self, dp):
        """Delete all existing OpenFlow rules from `dp` before reprogramming paths."""
        ofp = dp.ofproto
        parser = dp.ofproto_parser

        # Wildcard match with OFPFC_DELETE clears stale rules on the switch
        dp.send_msg(parser.OFPFlowMod(
            datapath=dp,
            command=ofp.OFPFC_DELETE,
            out_port=ofp.OFPP_ANY,
            out_group=ofp.OFPG_ANY,
            match=parser.OFPMatch()
        ))

    # Install primary or backup path
    def install_path(self):
        """Program bidirectional forwarding rules for whichever path is currently active."""
        # Wait until all 4 topology switches (s1, s2, s3, s4) have connected
        if len(self.datapaths) < 4:
            return

        # Select port pairs (ingress_from_h1, egress_toward_h2) per switch DPID
        if self.active_path == 'primary':
            routes = {
                1: (1, 2),  # s1: port 1 (h1) <-> port 2 (s2)
                2: (1, 2),  # s2: port 1 (s1) <-> port 2 (s4)
                4: (2, 1)   # s4: port 2 (s2) <-> port 1 (h2)
            }
        else:
            routes = {
                1: (1, 3),  # s1: port 1 (h1) <-> port 3 (s3)
                3: (1, 2),  # s3: port 1 (s1) <-> port 2 (s4)
                4: (3, 1)   # s4: port 3 (s3) <-> port 1 (h2)
            }

        # Flush old flow entries across all switches to avoid stale loops or blackholes
        for dp in self.datapaths.values():
            self.clear_flows(dp)

        # Install symmetric bidirectional flow rules on every switch along the chosen path
        for dpid, (in_port, out_port) in routes.items():
            dp = self.datapaths[dpid]
            self.add_flow(dp, in_port, out_port)
            self.add_flow(dp, out_port, in_port)

        self.logger.info(
            "Installed %s path", self.active_path
        )

    # Detect switch connections
    @set_ev_cls(
        ofp_event.EventOFPSwitchFeatures,
        CONFIG_DISPATCHER
    )
    def switch_connected(self, ev):
        """Register each switch upon handshake and install path once all 4 are online."""
        dp = ev.msg.datapath
        self.datapaths[dp.id] = dp

        self.logger.info("Switch %s connected", dp.id)
        self.install_path()

    # Detect primary link failure
    @set_ev_cls(
        ofp_event.EventOFPPortStatus,
        MAIN_DISPATCHER
    )
    def port_status(self, ev):
        """Monitor port-status events on s1 port 2 and reroute to backup on link down."""
        dp = ev.msg.datapath
        port = ev.msg.desc

        # Filter strictly for the primary trunk interface on switch s1 (s1-eth2)
        if dp.id != 1 or port.port_no != 2:
            return

        ofp = dp.ofproto
        # Check OpenFlow 1.3 link-state and administrative port-down flags
        down = bool(
            (port.state & ofp.OFPPS_LINK_DOWN) or
            (port.config & ofp.OFPPC_PORT_DOWN)
        )

        # Trigger one-time failover from primary to backup when s1-eth2 goes down
        if down and self.active_path == 'primary':
            start = time.monotonic()

            self.logger.warning(
                "Primary link failed!"
            )

            self.active_path = 'backup'
            self.install_path()

            # Measure controller-side processing and FlowMod dispatch latency
            elapsed = time.monotonic() - start
            self.logger.info(
                "Controller processing time: %.6f seconds",
                elapsed
            )
