from shaptools import netweaver

nw = netweaver.NetweaverInstance('ha1', '00', 'your_password')

print nw.is_installed()