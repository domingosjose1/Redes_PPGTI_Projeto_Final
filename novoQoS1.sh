#!/bin/bash

for r in r1 r2 r3 r4; do
  pid=$(pgrep -f "mininet:$r")
  if [ -z "$pid" ]; then
    echo "⚠️  Nó $r não encontrado (talvez não esteja rodando no Mininet)."
    continue
  fi

  for intf in $(mnexec -a "$pid" ip -o link | awk -F': ' '{print $2}' | grep -v lo | sed 's/@.*//'); do
    echo "🔧 Configurando $r → $intf"
    
    # Remove qualquer configuração existente
    mnexec -a "$pid" tc qdisc del dev "$intf" root 2>/dev/null

    # 1. Cria o root HTB com limite total de 100 Mbps
    mnexec -a "$pid" tc qdisc add dev "$intf" root handle 1: htb default 30
    mnexec -a "$pid" tc class add dev "$intf" parent 1: classid 1:1 htb rate 100mbit ceil 100mbit

    # 2. Classe para tráfego prioritário (portas 12345 e 12346) – até 90 Mbps
    mnexec -a "$pid" tc class add dev "$intf" parent 1:1 classid 1:10 htb rate 90mbit ceil 100mbit prio 0

    # 3. Classe para tráfego iperf (porta 5001) – exatamente 5 Mbps
    mnexec -a "$pid" tc class add dev "$intf" parent 1:1 classid 1:20 htb rate 5mbit ceil 5mbit prio 1

    # 4. Classe padrão para o restante – usa o restante (5 Mbps, sem prioridade)
    mnexec -a "$pid" tc class add dev "$intf" parent 1:1 classid 1:30 htb rate 5mbit ceil 100mbit prio 2

    # 5. Filtros para as classes
    #  Prioridade alta → tráfego portas 12345 e 12346
    mnexec -a "$pid" tc filter add dev "$intf" protocol ip parent 1: prio 1 u32 match ip dport 12345 0xffff flowid 1:10
    mnexec -a "$pid" tc filter add dev "$intf" protocol ip parent 1: prio 1 u32 match ip dport 12346 0xffff flowid 1:10

    #  Tráfego iperf → porta 5001
    mnexec -a "$pid" tc filter add dev "$intf" protocol ip parent 1: prio 2 u32 match ip dport 5001 0xffff flowid 1:20

    #  Todo o restante → classe padrão
    mnexec -a "$pid" tc filter add dev "$intf" protocol ip parent 1: prio 10 u32 match ip dport 0 0x0 flowid 1:30
  done
done
