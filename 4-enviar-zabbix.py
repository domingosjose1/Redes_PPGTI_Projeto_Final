import re
import time
import subprocess
from collections import deque

ARQUIVO_ENTRADA = "resultado.txt"
ZABBIX_SERVER = "192.168.0.20"
HOSTNAME = "Monitoramento"

# === Variáveis configuráveis ===
LIMIAR_LATENCIA_MS = 5
TEMPO_INICIO_QOS = 60          # segundos após o início do script
TEMPO_PERMANENCIA_QOS = 40     # tempo mínimo de permanência do QoS (segundos)

# === Controle interno ===
fila_latencia = deque(maxlen=5)
ids_processados = set()
linha_atual = 0
qos_ativo = False
tempo_qos_ativado = None
tempo_ultima_remocao_qos = None
inicio_monitoramento = time.time()


def enviar_para_zabbix(valor, chave):
    metric = f"{HOSTNAME} {chave} {valor:.3f}"
    try:
        result = subprocess.run(
            ["zabbix_sender", "-z", ZABBIX_SERVER, "-i", "-"],
            input=metric,
            text=True,
            capture_output=True
        )
        print(f"[Zabbix] Enviado: {chave} = {valor:.3f} | Resposta: {result.stdout.strip()}")
    except Exception as e:
        print(f"[Zabbix] Erro ao enviar para chave {chave}: {e}")


def aplicar_qos():
    print("[QoS] Ativando regra de QoS...")
    subprocess.run(["bash", "./novoQoS1.sh"])


def remover_qos():
    print("[QoS] Removendo regra de QoS...")
    subprocess.run(["bash", "./novoQoS-remover.sh"])


def verificar_qos():
    global qos_ativo, tempo_qos_ativado, tempo_ultima_remocao_qos

    if len(fila_latencia) < fila_latencia.maxlen:
        return

    media = sum(fila_latencia) / len(fila_latencia)
    print(f"[Média] Últimos 5 pacotes = {media:.3f} ms")

    tempo_rodando = time.time() - inicio_monitoramento
    tempo_desde_remocao = (time.time() - tempo_ultima_remocao_qos) if tempo_ultima_remocao_qos else None

    if not qos_ativo:
        if tempo_rodando >= TEMPO_INICIO_QOS and media > LIMIAR_LATENCIA_MS:
            if tempo_ultima_remocao_qos is None or tempo_desde_remocao >= TEMPO_PERMANENCIA_QOS:
                aplicar_qos()
                qos_ativo = True
                tempo_qos_ativado = time.time()
            else:
                restante = TEMPO_PERMANENCIA_QOS - tempo_desde_remocao
                print(f"[QoS] Aguardando tempo após remoção para reativar... {restante:.1f}s restantes")

    elif qos_ativo:
        tempo_ativo = time.time() - tempo_qos_ativado
        tempo_restante = TEMPO_PERMANENCIA_QOS - tempo_ativo

        if tempo_ativo >= TEMPO_PERMANENCIA_QOS:
            if media <= LIMIAR_LATENCIA_MS:
                remover_qos()
                qos_ativo = False
                tempo_qos_ativado = None
                tempo_ultima_remocao_qos = time.time()
            else:
                print(f"[QoS] Mantendo QoS: latência ainda acima do limiar ({media:.3f} ms > {LIMIAR_LATENCIA_MS} ms)")
        else:
            print(f"[QoS] Aguardando permanência mínima: {tempo_restante:.1f}s restantes")


print("Iniciando leitura contínua de resultado.txt...")

while True:
    try:
        with open(ARQUIVO_ENTRADA, "r") as f:
            linhas = f.readlines()

            while linha_atual < len(linhas):
                linha = linhas[linha_atual]

                if "Pacote ID" in linha:
                    id_match = re.search(r"Pacote ID (\d+)", linha)
                    if id_match:
                        pkt_id = int(id_match.group(1))

                elif "Tempo total acumulado até aqui:" in linha:
                    tempo_match = re.search(r"Tempo total acumulado até aqui: ([0-9.]+)", linha)
                    if tempo_match and pkt_id not in ids_processados:
                        total = float(tempo_match.group(1))

                        # Envia ao Zabbix
                        if pkt_id < 2000:
                            enviar_para_zabbix(total, "metrica.h1")
                        else:
                            enviar_para_zabbix(total, "metrica.h2")

                        # Adiciona à fila e verifica regra de QoS
                        fila_latencia.append(total)
                        verificar_qos()

                        ids_processados.add(pkt_id)

                linha_atual += 1

    except FileNotFoundError:
        print(f"[Erro] Arquivo {ARQUIVO_ENTRADA} ainda não existe.")
    except Exception as e:
        print(f"[Erro inesperado] {e}")

    time.sleep(1)
