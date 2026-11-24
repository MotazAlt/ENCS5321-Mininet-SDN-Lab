# Task 2 — Mininet CLI Commands (`tc`, `iperf`, `ping`)

Launch the bottleneck topology:

```bash
sudo python3 task2_congestion_aqm/task2.py
```

## 1. Verify Topology, Connectivity, and 10 Mb/s HTB Bottleneck

```text
mininet> net
mininet> pingall
mininet> sh tc class show dev s1-eth4
```

Expected HTB class on `s1-eth4`:

```text
class htb 5:1 root prio 0 rate 10Mbit ceil 10Mbit burst 15kb cburst 1600b
```

## 2. Start `iperf` TCP & UDP Servers on Receiver `h4`

```text
mininet> h4 iperf -s -p 5001 > /tmp/tcp_server.txt 2>&1 &
mininet> h4 iperf -s -u -p 5002 > /tmp/udp_server.txt 2>&1 &
```

## 3. Experiment A — Drop-Tail FIFO (`pfifo`, limit 100 packets)

Configure FIFO under HTB parent class `5:1` and verify initial counters:

```text
mininet> sh tc qdisc replace dev s1-eth4 parent 5:1 handle 10: pfifo limit 100
mininet> sh tc -s qdisc show dev s1-eth4
```

Run simultaneous 30 s TCP (`h1 -> h4`), UDP (`h2 -> h4`, requested `-b 15M`), and continuous ICMP ping (`h1 -> h4`), then inspect results:

```text
mininet> h1 iperf -c 10.0.0.4 -p 5001 -t 30 -i 1 > /tmp/tcp_fifo2.txt 2>&1 &
mininet> h2 iperf -c 10.0.0.4 -u -p 5002 -b 15M -t 30 -i 1 > /tmp/udp_fifo2.txt 2>&1 &
mininet> h1 ping -i 0.2 -c 150 h4 > /tmp/ping_fifo2.txt 2>&1 &
mininet> sh sleep 33
mininet> h1 tail -n 6 /tmp/tcp_fifo2.txt
mininet> h2 tail -n 9 /tmp/udp_fifo2.txt
mininet> h1 tail -n 5 /tmp/ping_fifo2.txt
mininet> sh tc -s qdisc show dev s1-eth4
```

## 4. Experiment B — Random Early Detection (`red`)

Configure RED under HTB parent class `5:1` and verify zero initial drop counters:

```text
mininet> sh tc qdisc replace dev s1-eth4 parent 5:1 handle 20: red limit 150000 min 30000 max 90000 avpkt 1000 burst 31 probability 0.02 bandwidth 10Mbit
mininet> sh tc -s qdisc show dev s1-eth4
```

Run the simultaneous 30 s TCP, UDP, and ICMP workload and inspect results:

```text
mininet> h1 iperf -c 10.0.0.4 -p 5001 -t 30 -i 1 > /tmp/tcp_red.txt 2>&1 &
mininet> h2 iperf -c 10.0.0.4 -u -p 5002 -b 15M -t 30 -i 1 > /tmp/udp_red.txt 2>&1 &
mininet> h1 ping -i 0.2 -c 150 h4 > /tmp/ping_red.txt 2>&1 &
mininet> sh sleep 33
mininet> h1 tail -n 6 /tmp/tcp_red.txt
mininet> h2 tail -n 10 /tmp/udp_red.txt
mininet> h1 tail -n 5 /tmp/ping_red.txt
mininet> sh tc -s qdisc show dev s1-eth4
```
