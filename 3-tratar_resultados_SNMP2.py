import re
import time
from collections import defaultdict

ARQUIVO_ENTRADA = "monitoramento_pacotes.txt"
ARQUIVO_SAIDA = "resultado.txt"
ROTEADOR_ORDEM = ["r1", "r2", "r3", "r4"]
NUMERO_MINIMO_ROTEADORES = 3

dados_pacotes = defaultdict(dict)
ids_processados = set()

def processar_arquivo():
    id_atual = None
    with open(ARQUIVO_ENTRADA, "r") as f:
        for linha in f:
            id_match = re.match(r".*Pacote ID (\d+).*", linha)
            rota_match = re.match(r"- (r\d+)\s+: chegada: ([0-9.]+) \| saída: ([0-9.]+) \| delay: ([0-9.]+)s", linha)

            if id_match:
                id_atual = id_match.group(1)

            if rota_match and id_atual:
                if id_atual in ids_processados:
                    continue
                roteador, chegada, saida, delay = rota_match.groups()
                dados_pacotes[id_atual][roteador] = {
                    "chegada": float(chegada),
                    "saida": float(saida),
                    "delay": float(delay)
                }

    with open(ARQUIVO_SAIDA, "a") as f:
        for pkt_id in sorted(dados_pacotes.keys(), key=lambda x: int(x)):
            if pkt_id in ids_processados:
                continue
            if len(dados_pacotes[pkt_id]) < NUMERO_MINIMO_ROTEADORES:
                continue
            total = 0.0
            f.write(f"\n📦 Pacote ID {pkt_id} | Rastro temporal:\n")
            for r in ROTEADOR_ORDEM:
                if r in dados_pacotes[pkt_id]:
                    info = dados_pacotes[pkt_id][r]
                    delay_ms = info["delay"] * 1000
                    total += delay_ms
                    f.write(f"- {r:<4}: chegada: {info['chegada']:.6f} | saída: {info['saida']:.6f} | delay: {delay_ms:.3f} ms\n")
            f.write(f"Tempo total acumulado até aqui: {total:.3f} ms\n")
            f.write("─" * 46 + "\n")
            ids_processados.add(pkt_id)

print("Aguardando conteúdo no arquivo...")
while True:
    try:
        with open(ARQUIVO_ENTRADA, "r") as f:
            if len(f.readlines()) > 0:
                break
    except FileNotFoundError:
        pass
    time.sleep(5)

print("Iniciando monitoramento contínuo...")
open(ARQUIVO_SAIDA, "w").write("Iniciando monitoramento geral\n")

time.sleep(5)  # ⏱️ Aguarda antes de iniciar leitura real

while True:
    processar_arquivo()
