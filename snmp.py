from pysnmp.hlapi import *

def snmp_walk(ip, community='public'):
    for (errorIndication,
         errorStatus,
         errorIndex,
         varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=1),
            UdpTransportTarget((ip, 161), timeout=2, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1')),
            lexicographicMode=False):

        if errorIndication:
            print(f"Erro: {errorIndication}")
            break

        if errorStatus:
            print(
                f"Erro SNMP: {errorStatus.prettyPrint()} "
                f"no índice {errorIndex}"
            )
            break

        for oid, value in varBinds:
            print(f"{oid} = {value}")

snmp_walk("189.74.138.6")