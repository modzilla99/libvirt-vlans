#!/usr/bin/python3

import os
import subprocess
import sys
from time import sleep
import xml.etree.cElementTree as xml

class interface:
    def __init__(self):
        self.name = "invalid"
        self.pvid = 1
        self.untagged = 1
        self.tagged = []
        self.bridge = "virbr0"
    def name(self):
        return(self.name)
    def pvid(self):
        return(self.pvid)
    def untagged(self):
        return(self.untagged)
    def tagged(self):
        return(self.tagged)
    def bridge(self):
        return(self.bridge)
    def mac(self):
        return(self.mac)

    def set_name(self, setting):
        self.name = setting
    def set_pvid(self, setting):
        self.pvid = int(setting)
    def set_untagged(self, setting):
        self.untagged = int(setting)
    def set_tagged(self, setting):
        self.tagged.append(int(setting))
    def set_bridge(self, setting):
        self.bridge = setting
    def set_mac(self, setting):
        self.mac = setting

def loadXML(file):
    this = xml.ElementTree(file=file)
    return this


def main():
    try:
        vm_xml = loadXML("/etc/libvirt/qemu/%s.xml" % sys.argv[1]).getroot()
    except:
        print("Error loading XML..")
        exit(1)

    print("Successfully loaded XML")

    intfCount = 0
    for interfaces in vm_xml.findall('./metadata/{https://github.com/modzilla99/libvirt-vlans}vlanconfig/{https://github.com/modzilla99/libvirt-vlans}iface'):
        intf = interface()

        try:
            libvirt_interface = vm_xml.findall('./devices/interface[@type="bridge"]')[intfCount]
        except Exception as e:
            print("Error: ", e)
            exit(1)

        print("Starting configuration of Interface%s" % intfCount)
        try:
            intf.set_mac(libvirt_interface.findall('./mac')[0].attrib['address'])
            intf.set_bridge(libvirt_interface.findall('./source')[0].attrib['bridge'])
        except Exception as e:
            print("Error: ", e)
            exit(1)

        os_networking = subprocess.run(["sh","-c","ip -br l | awk '{print $1 \" \" $3}'"], stdout=subprocess.PIPE, text=True).stdout

        for phyint in os_networking.splitlines():
            phyint = phyint.split(" ")
            
            phymac = phyint[1].split(":")
            phymac = phymac[1], phymac[2], phymac[3], phymac[4], phymac[5]

            virtmac = intf.mac.split(":")
            virtmac = virtmac[1], virtmac[2], virtmac[3], virtmac[4], virtmac[5]

            if phymac == virtmac:
                intf.set_name(phyint[0])

        if intf.name == "invalid":
            print("Error: Virtual Interface could not be found")
            exit(1)

        try:
            intf.set_pvid((interfaces.attrib)['pvid'])
        except:
            intf.set_pvid(0)
        
        for vlan in interfaces.findall('{https://github.com/modzilla99/libvirt-vlans}vlan'):
            try:
                vlan_tag = (vlan.attrib)['untagged']
            except:
                vlan_tag = "no"
            
            if vlan_tag == "yes":
                intf.set_untagged(vlan.text)
            elif vlan_tag == "no":
                intf.set_tagged(vlan.text)

        cmd = "bridge vlan del vid 1 dev %s && bridge vlan add vid %s dev %s pvid untagged" % ( intf.name, intf.untagged, intf.name)
        print("Setting untagged VLAN %s on interface %s" % (intf.name, intf.untagged))
        subprocess.run(["sh","-c",cmd], stdout=subprocess.PIPE, text=True)

        for bridge_vlan in intf.tagged:
            cmd = "bridge vlan add vid %s dev %s" % ( bridge_vlan, intf.name)
            print("Setting tagged VLAN %s on interface %s" % (intf.name, bridge_vlan))
            subprocess.run(["sh","-c",cmd], stdout=subprocess.PIPE, text=True)

        print("Interface %s was successfully set up" % intf.name)
        intfCount += 1

main()