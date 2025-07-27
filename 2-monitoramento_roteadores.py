# monitor_router.py
from scapy.all import sniff, Raw, IP, get_if_list
import time
import json
import os
from threading import Thread
from collections import defaultdict

ROUTER_ID = os.getenv("ROUTER_ID", "rX")
LOG_FILE = "monitoramento_pacotes.txt"

# Marcar início apenas uma vez
if os.getenv("CLEAR_LOG", "1") == "1" and ROUTER_ID == "r1":
    with open(LOG_FILE, "w") as f:
        f.write("Iniciando monitoramento geral\n")

# Armazena dados completos de cada pacote
full_packet_data = defaultdict(dict)
# Controle para evitar múltiplas escritas do mesmo pacote
pacotes_escritos = set()

# Ordem fixa dos roteadores
ROUTER_ORDER = ["r1", "r2", "r3", "r4"]

def salvar_log_final(pkt_id):
    try:
        # Atualiza dados do roteador atual
        if ROUTER_ID in full_packet_data[pkt_id]:
            full_packet_data[pkt_id][ROUTER_ID].update(packet_data[pkt_id][ROUTER_ID])
        else:
            full_packet_data[pkt_id][ROUTER_ID] = packet_data[pkt_id][ROUTER_ID]

        # Impede múltiplas gravações
        if pkt_id in pacotes_escritos:
            return

        # Verifica se há pelo menos uma entrada com chegada e saída
        algum_completo = any("arrival" in rdata and "departure" in rdata for rdata in full_packet_data[pkt_id].values())
        if not algum_completo:
            return

        with open(LOG_FILE, "a") as f:
            f.write(f"\n📦 Pacote ID {pkt_id} | Rastro temporal:\n")
            for router in ROUTER_ORDER:
                if router in full_packet_data[pkt_id]:
                    rdata = full_packet_data[pkt_id][router]
                    if "arrival" in rdata and "departure" in rdata:
                        delay = rdata["departure"] - rdata["arrival"]
                        f.write(f"- {router:<4}: chegada: {rdata['arrival']:.6f} | saída: {rdata['departure']:.6f} | delay: {delay:.6f}s\n")
            f.write("─" * 46 + "\n")

        pacotes_escritos.add(pkt_id)

    except Exception as e:
        print(f"[{ROUTER_ID}] Erro ao escrever no log: {e}")

packet_data = defaultdict(dict)

def handle(pkt):
    if Raw in pkt and IP in pkt:
        try:
            payload = json.loads(pkt[Raw].load.decode())
            pkt_id = str(payload.get("id", "sem_id"))
            now = time.time()

            if ROUTER_ID not in packet_data[pkt_id]:
                packet_data[pkt_id][ROUTER_ID] = {"arrival": now}
                print(f"\n🛼 [{ROUTER_ID}] Pacote ID {pkt_id} | chegada: {now:.6f}")
            elif "departure" not in packet_data[pkt_id][ROUTER_ID]:
                packet_data[pkt_id][ROUTER_ID]["departure"] = now
                print(f"\n🛼 [{ROUTER_ID}] Pacote ID {pkt_id} | saída: {now:.6f}")
                salvar_log_final(pkt_id)

        except Exception as e:
            print(f"[{ROUTER_ID}] Erro ao processar pacote: {e}")

interfaces = [i for i in get_if_list() if not i.startswith("lo")]
print(f"[{ROUTER_ID}] Escutando nas interfaces: {interfaces}")

def start_sniff(iface):
    sniff(filter="tcp and (port 12345 or port 12346)", prn=handle, iface=iface, store=False)

for iface in interfaces:
    Thread(target=start_sniff, args=(iface,), daemon=True).start()

while True:
    time.sleep(1)
