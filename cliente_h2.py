# cliente_h2.py
from scapy.all import *
import time
import json

pkt_id = 2001
while True:
    payload = json.dumps({"id": pkt_id})
    pkt = IP(dst="192.168.3.2")/TCP(dport=12346, sport=RandShort())/Raw(load=payload)
    send(pkt, verbose=0)
    print(f"Enviado pacote ID {pkt_id}")
    pkt_id += 1
    time.sleep(1)
