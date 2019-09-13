from shaptools import netweaver

netweaver.NetweaverInstance.update_conf_file(
    '/root/dev/shaptools/experiments/test.inifile.params', **{'sid': 'HA1', 'hostname': 'hacert01', 'masterPwd': 'Simran123'})
