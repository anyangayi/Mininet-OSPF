#!/usr/bin/python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import Intf
import time
import os

class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()
	
class NetworkTopo( Topo ):
    "A LinuxRouter connecting three IP subnets"

    def build( self, **_opts ):

	# Initialize topology
    L1 = 140         # numbers of router
	L2 = 126         # true numbers of router
	R1 = 14          # numbers of row
	C1 = 9           # numbers of col
    r = []
	defaultIP_first = '193.168.1.1/24'
	defaultIP_last = '193.168.10.2/24'

	# add router (first, last, 0 to L1-1): 
	router_first = self.addNode('rf', cls=LinuxRouter, ip=defaultIP_first) #first router
	router_last = self.addNode('rl', cls=LinuxRouter, ip=defaultIP_last) #last router
	for k in range( L1 ):
		defaultIP = '193.168.{}.2/24'.format( k+1 )
		router = self.addNode( 'r{}'.format(k), cls=LinuxRouter, ip=defaultIP)
		r.append( router )

        # add host  
        #h1 = self.addHost( 'h1', ip='193.168.1.100/24', defaultRoute='via 193.168.1.1') #define gateway

	# add link (rf to 0, 10, ..., 130): ip1 = '193.168.1.1/24' for rf-eth1, ip2 = '193.168.1.2/24' for r0-eth1
	for j in range( R1 ):
		router1 = router_first
		router2 = r[j*10]
		port1 = 'rf-eth{}'.format( j+1 )
		port2 = 'r{}-eth1'.format( j*10 )
		defaultIP1 = '193.168.{}.1/24'.format( j*10+1 )
		defaultIP2 = '193.168.{}.2/24'.format( j*10+1 )
		self.addLink(router1, router2, intfName1=port1, params1={ 'ip' : defaultIP1 }, intfName2=port2, params2={ 'ip' : defaultIP2 })
	
	# add link (0 to 8, 10 to 18, ..., 130 to 138): ip1 = '193.168.2.1/24' for r0-eth2, ip2 = '193.168.2.2/24' for r1-eth1
	for j in range( R1 ):
		for i in range( 1, C1 ):
			router1 = r[j*10+i-1]
                	router2 = r[j*10+i]
			port1 = 'r{}-eth2'.format( j*10+i-1 )
			port2 = 'r{}-eth1'.format( j*10+i )
			defaultIP1 = '193.168.{}.1/24'.format( j*10+i+1 )
			defaultIP2 = '193.168.{}.2/24'.format( j*10+i+1 )
			#self.addLink(router1, router2, intfName1=port1, intfName2=port2, params2={ 'ip' : defaultIP2 })		
			self.addLink(router1, router2, intfName1=port1, params1={ 'ip' : defaultIP1 }, intfName2=port2, params2={ 'ip' : defaultIP2 })

	# add link (8, 18, ..., 138 to fl): ip1 = '193.168.10.1/24' for r8-eth2, ip2 = '193.168.10.2/24' for rl-eth1
	for j in range( R1 ):	
		router3 = r[j*10+8]
		router4 = router_last
		port3 = 'r{}-eth2'.format( j*10+8 )
		port4 = 'rl-eth{}'.format( j+1 )
		defaultIP3 = '193.168.{}.1/24'.format( (j+1)*10 )
		defaultIP4 = '193.168.{}.2/24'.format( (j+1)*10 )
		self.addLink(router3, router4, intfName1=port3, params1={ 'ip' : defaultIP3 }, intfName2=port4, params2={ 'ip' : defaultIP4 })
	
	#self.addLink(h1,router1,intfName2='r1-eth1',params2={ 'ip' : '193.168.1.1/24' })#params2 define the eth2 ip address

def run():
	topo = NetworkTopo()
	net = Mininet(controller = None, topo=topo )	
	L1 = 140         # numbers of router
	r_f=net.getNodeByName('rf')
	r_l=net.getNodeByName('rl')
	Intf('enxf8e43b1d8202', node=r_f)
	Intf('enxf8e43b1dd5e1', node=r_l)
	
	net.start()
	info('starting zebra and ospfd service:\n')
	r_f.cmd('ifconfig enxf8e43b1d8202 193.168.0.1/24')  #!!
	r_l_cmd = 'ifconfig enxf8e43b1dd5e1 193.168.{}.2/24'.format( L1+10 )
	r_l.cmd(r_l_cmd)

	r_f_zebra_cmd = 'zebra -f /usr/local/etc/rectangle-conf/rfzebra.conf -d -z /run/quagga/rfzebra.api -i /run/quagga/rfzebra.interface'
	r_f_ospfd_cmd = 'ospfd -f /usr/local/etc/rectangle-conf/rfospfd.conf -d -z /run/quagga/rfzebra.api -i /run/quagga/rfospfd.interface'
	r_l_zebra_cmd = 'zebra -f /usr/local/etc/rectangle-conf/rlzebra.conf -d -z /run/quagga/rlzebra.api -i /run/quagga/rlzebra.interface'
	r_l_ospfd_cmd = 'ospfd -f /usr/local/etc/rectangle-conf/rlospfd.conf -d -z /run/quagga/rlzebra.api -i /run/quagga/rlospfd.interface'
	r_f.cmd(r_f_zebra_cmd)
	time.sleep(0.5)#time for zebra to create api socket
	r_f.cmd(r_f_ospfd_cmd)
	r_l.cmd(r_l_zebra_cmd)
	time.sleep(0.5)#time for zebra to create api socket
	r_l.cmd(r_l_ospfd_cmd)

	for k in range( L1 ):
		router_name = 'r{}'.format( k )
		zebra_command = 'zebra -f /usr/local/etc/rectangle-conf/r{0}zebra.conf -d -z /run/quagga/r{0}zebra.api -i /run/quagga/r{0}zebra.interface'.format( k )
		ospfd_command = 'ospfd -f /usr/local/etc/rectangle-conf/r{0}ospfd.conf -d -z /run/quagga/r{0}zebra.api -i /run/quagga/r{0}ospfd.interface'.format( k )
		router = net.getNodeByName(router_name)
		router.cmd(zebra_command)
		time.sleep(0.5)#time for zebra to create api socket
		router.cmd(ospfd_command)

	CLI( net )
	net.stop()
	os.system("killall -9 ospfd zebra")
	os.system("rm -f *api*")
	os.system("rm -f *interface*")

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()

