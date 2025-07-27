from mininet.net import Mininet
from mininet.node import Node
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

def addRouter(net, name):
    return net.addHost(name, cls=Node, ip='0.0.0.0')

def enableRouting(router):
    router.cmd('sysctl -w net.ipv4.ip_forward=1')

def topology():
    net = Mininet(link=TCLink)

    # Hosts
    h1 = net.addHost('h1', ip='192.168.1.2/24', defaultRoute='via 192.168.1.1')
    h2 = net.addHost('h2', ip='192.168.2.2/24', defaultRoute='via 192.168.2.1')
    h3 = net.addHost('h3', ip='192.168.3.2/24', defaultRoute='via 192.168.3.1')

    # Roteadores de borda
    r1 = addRouter(net, 'r1')  # Conecta h1
    r3 = addRouter(net, 'r3')  # Conecta h2
    r4 = addRouter(net, 'r4')  # Conecta h3

    # Roteadores intermediários
    r2 = addRouter(net, 'r2')

    # Conectando hosts aos roteadores
    net.addLink(h1, r1, intfName1='h1-eth0', params1={'ip': '192.168.1.2/24'},
                         intfName2='r1-eth0', params2={'ip': '192.168.1.1/24'}, bw=100)
    net.addLink(h2, r3, intfName1='h2-eth0', params1={'ip': '192.168.2.2/24'},
                         intfName2='r3-eth0', params2={'ip': '192.168.2.1/24'}, bw=100)
    net.addLink(h3, r4, intfName1='h3-eth0', params1={'ip': '192.168.3.2/24'},
                         intfName2='r4-eth0', params2={'ip': '192.168.3.1/24'}, bw=100) 

    # Enlaces ponto a ponto /30
    net.addLink(r1, r2, intfName1='r1-eth1', params1={'ip': '10.0.1.1/30'},
                         intfName2='r2-eth0', params2={'ip': '10.0.1.2/30'}, bw=100)

    net.addLink(r2, r4, intfName1='r2-eth1', params1={'ip': '10.0.4.1/30'},
                         intfName2='r4-eth1', params2={'ip': '10.0.4.2/30'}, bw=100)

    net.addLink(r2, r3, intfName1='r2-eth2', params1={'ip': '10.0.3.1/30'},
                         intfName2='r3-eth2', params2={'ip': '10.0.3.2/30'}, bw=100)

    net.addLink(r1, r3, intfName1='r1-eth2', params1={'ip': '10.0.2.1/30'},
                         intfName2='r3-eth1', params2={'ip': '10.0.2.2/30'}, bw=100)



    print("*** Iniciando rede")
    net.start()

    # Forçar IP em r2-eth0
    r2.cmd('ifconfig r2-eth0 10.0.1.2/30 up')

    # Forçar IPs nas interfaces de borda
    r1.cmd('ifconfig r1-eth0 192.168.1.1/24 up')
    r3.cmd('ifconfig r3-eth0 192.168.2.1/24 up')
    r4.cmd('ifconfig r4-eth0 192.168.3.1/24 up')

    print("*** Habilitando roteamento")
    for router in [r1, r2, r3, r4]:
        enableRouting(router)

    print("*** Configurando rotas estáticas")
    r1.cmd('ip route add 192.168.2.0/24 via 10.0.2.2')
    r1.cmd('ip route add 192.168.3.0/24 via 10.0.1.2')

    r3.cmd('ip route add 192.168.1.0/24 via 10.0.2.1')
    r3.cmd('ip route add 192.168.3.0/24 via 10.0.3.1')

    r4.cmd('ip route add 192.168.1.0/24 via 10.0.4.1')
    r4.cmd('ip route add 192.168.2.0/24 via 10.0.4.1')

    r2.cmd('ip route add 192.168.1.0/24 via 10.0.1.1')
    r2.cmd('ip route add 192.168.2.0/24 via 10.0.3.2')
    r2.cmd('ip route add 192.168.3.0/24 via 10.0.4.2')

    print("*** Iniciando testes com iperf")
   #h1.cmd('iperf -s -D')
   #h2.cmd('iperf -s -D')
    h3.cmd('iperf -s -D')


    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
