import ssl
import requests
from jsonrpclib import Server

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

def setHostname(host_ip):
    hostname = "veos-oci-" + host_ip.replace('.','-')
    switch = Server("https://cvpadmin:arista123@" + host_ip + "/command-api" )
    response = switch.runCmds(1, ["enable", 
        "configure", 
        "hostname " + hostname, 
        "interface loopback 0", 
        "ip address " + host_ip + "/32", 
        "no shutdown"])
    return hostname

def addInstanceCvp(host_ip):
    print("Adding to CVP : " + host_ip)
    r = requests.post('http://localhost:8080/routercvp/', json = {'ipAddress':host_ip})
    print(r)
    return r

setHostname("129.213.103.108")
#addInstanceCvp("129.213.103.108")
