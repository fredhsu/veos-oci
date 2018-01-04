import os
import oci
from time import sleep

config = oci.config.from_file()

compartment_id = "ocid1.tenancy.oc1..aaaaaaaaawiselp4yjvnsjxr6cwabw2lvefolabds5tufevvbuojbf3s7kdq"
subnet_id = "ocid1.subnet.oc1.phx.aaaaaaaaursbyjzlzmff5a2otmlouuq3kiojckiovzqcsy4comnao3vizloa"
image_id = "ocid1.image.oc1.phx.aaaaaaaacv5sgh7zwvnjfzq72eltwtzkwrv4vhr2ashl6dq2gqnm3fe3a6ua"
compute = oci.core.compute_client.ComputeClient(config)
vnet = oci.core.virtual_network_client.VirtualNetworkClient(config)
response = compute.list_instances(compartment_id)
for value in response.data:
    # print(value)
    vnics = compute.list_vnic_attachments(compartment_id, instance_id = value.id)
    for v in vnics.data:
        print(v)
        #vnic = vnet.get_vnic(v.vnic_id)
        #print("private ip: " + vnic.data.private_ip)
        #print("public ip: " + vnic.data.public_ip)

source_details = oci.core.models.InstanceSourceViaImageDetails()
source_details.image_id = image_id

create_vnic_details = oci.core.models.CreateVnicDetails()
create_vnic_details.assign_public_ip = True
create_vnic_details.subnet_id = subnet_id

request = oci.core.models.LaunchInstanceDetails()
request.availability_domain = "qPIx:PHX-AD-1"
request.compartment_id = compartment_id
request.create_vnic_details = create_vnic_details
request.shape = "VM.Standard1.1"
request.source_details = source_details
request.display_name = "veos-oci-demo"

launch = compute.launch_instance(request)
print("## Launched Instance: ##")
new_instance = launch.data
print(new_instance)
sleep(5)
vnics = compute.list_vnic_attachments(compartment_id, instance_id = new_instance.id)
for v in vnics.data:
    vnic = vnet.get_vnic(v.vnic_id)
    print("private ip: " + vnic.data.private_ip)
    print("public ip: " + vnic.data.public_ip)
sleep(150)
