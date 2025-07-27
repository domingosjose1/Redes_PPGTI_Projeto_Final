#!/bin/bash

for r in r1 r2 r3 r4; do
  pid=$(pgrep -f "mininet:$r")
  if [ -z "$pid" ]; then
    echo "Nó $r não encontrado (talvez não esteja rodando no Mininet)."
    continue
  fi
  for intf in $(mnexec -a "$pid" ip -o link | awk -F': ' '{print $2}' | grep -v lo | sed 's/@.*//'); do
    echo "Sem QoS, sem priorização"
    # Remove qualquer configuração existente
    mnexec -a "$pid" tc qdisc del dev "$intf" root 2>/dev/null

    # Limita a interface a 100 Mbps (HTB simples, sem priorização de porta)
    mnexec -a "$pid" tc qdisc add dev "$intf" root handle 1: htb default 1
    mnexec -a "$pid" tc class add dev "$intf" parent 1: classid 1:1 htb rate 100mbit ceil 100mbit
  done
done

echo "Prioridades removidas."
