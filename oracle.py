import os
import oci
import requests
import ssl
from time import sleep
from flask import Flask
from flask import request
from flask import jsonify
from flask_cors import CORS
from jsonrpclib import Server

# Use these for corporate
compartment_id = "ocid1.tenancy.oc1..aaaaaaaaawiselp4yjvnsjxr6cwabw2lvefolabds5tufevvbuojbf3s7kdq"
subnet_id = "ocid1.subnet.oc1.phx.aaaaaaaaursbyjzlzmff5a2otmlouuq3kiojckiovzqcsy4comnao3vizloa"
image_id = "ocid1.image.oc1.phx.aaaaaaaaajgwxitqioomenesux4jfcjwosx5b523x22tffqv3m2howjknjbq"
profile_name = "DEFAULT"
avail_domain = "qPIx:PHX-AD-1"

# Use these for personal
# compartment_id = "ocid1.tenancy.oc1..aaaaaaaazco3xpwhyer3ayza5wl6uldqxulyqsdcmnvxykv4fr457n73c5rq"
# subnet_id = "ocid1.subnet.oc1.iad.aaaaaaaah3nz3q5szlpvuwiwdjer6pwzm6ur3mrnxgkt62yosiytemgreihq"
# image_id = "ocid1.image.oc1.iad.aaaaaaaacbgdflm66sxcdxriiatfrr27hb5wsy7hwg6wooocpsl7i3gld6ga" # fredcustom
# profile_name = "PERSONAL"
# avail_domain = "DESs:US-ASHBURN-AD-1"

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context



app = Flask(__name__)
CORS(app)

def create_instance(config, req):
    compute = oci.core.compute_client.ComputeClient(config)
    vnet = oci.core.virtual_network_client.VirtualNetworkClient(config)
    source_details = oci.core.models.InstanceSourceViaImageDetails()
    source_details.image_id = image_id

    create_vnic_details = oci.core.models.CreateVnicDetails()
    create_vnic_details.assign_public_ip = True
    create_vnic_details.subnet_id = subnet_id

    req.create_vnic_details = create_vnic_details
    req.source_details = source_details

    launch = compute.launch_instance(req)
    print("## Launched Instance: ##")
    new_instance = launch.data
    print(new_instance)
    sleep(30)
    vnics = compute.list_vnic_attachments(compartment_id, instance_id = new_instance.id)
    for v in vnics.data:
        vnic = vnet.get_vnic(v.vnic_id)
        print("private ip: " + vnic.data.private_ip)
        print("public ip: " + vnic.data.public_ip)
    sleep(150)
    setHostname(vnic.data.public_ip)
    addInstanceCvp(vnic.data.public_ip)
    return new_instance

def addInstanceCvp(host_ip):
    print("Adding to CVP : " + host_ip)
    r = requests.post('http://localhost:8080/routercvp/', json = {'ipAddress':host_ip})
    return r

def setHostname(host_ip):
    hostname = "veos-oci-" + host_ip.replace('.','-')
    print("Setting hostname to " + hostname)
    switch = Server("https://cvpadmin:arista123@" + host_ip + "/command-api" )
    success = False
    try:
        response = switch.runCmds( 1, ["enable", 
            "configure", 
            "hostname " + hostname,
            "ip name-server vrf default 8.8.8.8",
            "daemon TerminAttr" +
	    "exec /usr/bin/TerminAttr -ingestgrpcurl=162.210.129.23:9910 -taillogs -ingestauth=key," +
            "management api http-commands",
            "protocol http",
            "interface loopback 0", 
            "ip address " + host_ip + "/32", 
            "no shutdown"])
        print("configuration successful")
        success = true
    except:
        print("Did not connect, waiting 5 seconds")
        sleep(5)
        response = switch.runCmds( 1, ["enable", 
            "configure", 
            "hostname " + hostname,
            "ip name-server vrf default 8.8.8.8",
            "interface loopback 0", 
            "ip address " + host_ip + "/32", 
            "no shutdown"])
    return hostname

# def xcreate_instance(config, request):
#     compute = oci.core.compute_client.ComputeClient(config)
#     vnet = oci.core.virtual_network_client.VirtualNetworkClient(config)
#     source_details = oci.core.models.InstanceSourceViaImageDetails()
#     source_details.image_id = image_id

#     create_vnic_details = oci.core.models.CreateVnicDetails()
#     create_vnic_details.assign_public_ip = True
#     create_vnic_details.subnet_id = subnet_id

#     request = oci.core.models.LaunchInstanceDetails()
#     # request.availability_domain = "qPIx:PHX-AD-1"
#     request.availability_domain = "DESs:US-ASHBURN-AD-1"
#     request.compartment_id = compartment_id
#     request.create_vnic_details = create_vnic_details
#     request.shape = "VM.Standard1.2"
#     request.source_details = source_details
#     request.display_name = "veos-oci-demo"

#     launch = compute.launch_instance(request)
#     print("## Launched Instance: ##")
#     new_instance = launch.data
#     print(new_instance)
#     sleep(30)
#     vnics = compute.list_vnic_attachments(compartment_id, instance_id = new_instance.id)
#     for v in vnics.data:
#         vnic = vnet.get_vnic(v.vnic_id)
#         print("private ip: " + vnic.data.private_ip)
#         print("public ip: " + vnic.data.public_ip)
#     sleep(120)

@app.route('/oci/api/v1.0/vrouter', methods=['POST'])
def create_router():
    if request.method == 'POST':
        # config = oci.config.from_file(profile_name="PERSONAL")
        config = oci.config.from_file(profile_name=profile_name)
        print(request.json)
        req = oci.core.models.LaunchInstanceDetails()
        # req.availability_domain = request.json['availabilityDomain']
        req.availability_domain = avail_domain
        req.compartment_id = compartment_id
        req.shape = request.json['shape']
        req.shape = "VM.Standard1.2"
        req.display_name = request.json['name']
        new_instance = create_instance(config, req)
        return jsonify({'task':'complete'}), 201

if __name__ == '__main__':
    print("Running Oracle API server")
    app.run(debug=True)
