# Libvirt vlans

This project tries to ease the use of vlan tagging with linux bridges on libvirt. The idea and parts of my work are based on the great work of [Ingo](https://serverfault.com/questions/1051294/vlan-support-with-libvirt-for-linux-bridge-to-virtual-machines/1051295#1051295) on serverfault.


## Installation

Install the `qemu`-script to `/etc/libvirt/hooks/` and make it executable. Do the same for `vlan-config.py`.

```bash
mkdir /etc/libvirt/hooks/
cp qemu vlan-config.py /etc/libvirt/hooks/
chmod +x /etc/libvirt/hooks/{qemu,vlan-config.py}
```

Now `libvirtd` needs to be restarted to use the qemu script on vm start.

```bash
systemctl restart libvirtd
```

The qemu hook will log to `/var/log/libvirt/qemu/`.

## Preperation

To be able to set and foward VLAN tags you'll need a bridge that allows `vlan_filtering` and a bridge slave where the vid tags can egress. 

```shell
$ nmcli con sh bridge0
connection.id:                          bridge0
connection.uuid:                        95e4d2bb-01c0-499b-bdc1-570da5df1af4
connection.stable-id:                   --
connection.type:                        bridge
connection.interface-name:              bridge0
bridge.vlan-filtering:                  ja        # Important to turn on
bridge.vlan-default-pvid:               1         # Sets the default VLAN for the bridge0 interface
bridge.vlans:                           2-10     # Sets all allowed VLANs except pvid for bridge0 interface
```
```shell
$ nmcli con sh eno1
connection.id:                          eno1
connection.uuid:                        8255f4e3-add6-4097-9c3d-6f20e54b5008
connection.stable-id:                   --
connection.type:                        802-3-ethernet
connection.interface-name:              eno1
connection.master:                      bridge0
connection.slave-type:                  bridge
bridge-port.priority:                   32
bridge-port.path-cost:                  100
bridge-port.hairpin-mode:               nein
bridge-port.vlans:                      1 pvid untagged, 2-10    # Sets the default vid that egress will have and the allowed vids
```

To verify your vlan configuration you'll need to use the `bridge` command:

```shell
$ bridge vlan show
port              vlan-id  
eno1              1 PVID Egress Untagged
                  2
                  3
                  4
                  5
                  6
                  7
                  8
                  9
                  10
bridge0           1 PVID Egress Untagged
                  2
                  3
                  4
                  5
                  6
                  7
                  8
                  9
                  10
.
.
.
vnet31            38
                  50 PVID Egress Untagged
                  51
```


## Configuration

Have a look into `example.xml`. It's an example on how vlans get configured.

You need to add metadata information to the VM in order for the script to pick up the vlan ids. It should look something like this:

```xml
<metadata xmlns:ns0="https://github.com/modzilla99/libvirt-vlans">
  <ns0:vlanconfig>
    <ns0:iface pvid="1">
      <ns0:vlan untagged="yes">1</ns0:vlan>
      <ns0:vlan untagged="no">10</ns0:vlan>
      <ns0:vlan untagged="no">11</ns0:vlan>
    </ns0:iface>
    <ns0:iface pvid="13">
      <ns0:vlan untagged="no">1</ns0:vlan>
      <ns0:vlan untagged="no">10</ns0:vlan>
      <ns0:vlan untagged="yes">13</ns0:vlan>
      <ns0:vlan untagged="no">14-51</ns0:vlan>
    </ns0:iface>
  </ns0:vlanconfig>
</metadata>
```
To test whether your metadata edits have worked use the following command:
```bash
virsh metadata ${VMName} https://github.com/modzilla99/libvirt-vlans
```
The output should look something like this:
```xml
<vlanconfig>
  <iface pvid="1">
    <vlan untagged="yes">1</vlan>
    <vlan untagged="no">10-50</vlan>
  </iface>
  <iface pvid="50">
    <vlan untagged="no">38</vlan>
    <vlan untagged="yes">50</vlan>
    <vlan untagged="no">51</vlan>
  </iface>
</vlanconfig>
```