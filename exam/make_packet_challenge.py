"""Create a synthetic HTTP forensic PCAP; no traffic is sent."""
import argparse
import base64
import ipaddress
import json
from pathlib import Path
import secrets
import socket
import struct
import time
from urllib.parse import urlencode


def checksum(data):
    if len(data)%2:data+=b'\0'
    value=sum(struct.unpack('!'+str(len(data)//2)+'H',data))
    while value>>16:value=(value&65535)+(value>>16)
    return (~value)&65535


def packet(src,dst,sport,dport,seq,ack,flags,payload=b''):
    source=socket.inet_aton(src);destination=socket.inet_aton(dst)
    tcp=struct.pack('!HHIIBBHHH',sport,dport,seq,ack,80,flags,65535,0,0)
    pseudo=source+destination+struct.pack('!BBH',0,6,len(tcp)+len(payload))
    tcp=tcp[:16]+struct.pack('!H',checksum(pseudo+tcp+payload))+tcp[18:]
    ip=struct.pack('!BBHHHBBH4s4s',69,0,20+len(tcp)+len(payload),1,16384,64,6,0,source,destination)
    ip=ip[:10]+struct.pack('!H',checksum(ip))+ip[12:]
    ethernet=bytes.fromhex('00155d00002200155d0000130800')
    return ethernet+ip+tcp+payload


def create(path,client='10.10.10.13',server='10.10.10.22'):
    client=str(ipaddress.IPv4Address(client));server=str(ipaddress.IPv4Address(server))
    expected='BENCH-'+secrets.token_hex(8)
    frames=[]
    for i,(method,status,token) in enumerate((('POST',403,'DECOY-'+secrets.token_hex(8)),('POST',200,expected),('GET',200,'DECOY-'+secrets.token_hex(8)))):
        artifact=base64.b64encode(token.encode()).decode()
        body=urlencode(dict(user='training',artifact=artifact)).encode() if method=='POST' else b''
        uri='/api/collect' if method=='POST' else '/health?'+urlencode(dict(artifact=artifact))
        request=(f'{method} {uri} HTTP/1.1\r\nHost: ceh-benchmark.invalid\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: {len(body)}\r\n\r\n').encode()+body
        response=(f'HTTP/1.1 {status} '+('OK' if status==200 else 'Forbidden')+'\r\nContent-Length: 6\r\n\r\nstored').encode()
        port=51001+i;seq=1000+i*100;reply=5000+i*100
        frames.extend((packet(client,server,port,80,seq,0,2),packet(server,client,80,port,reply,seq+1,18),
            packet(client,server,port,80,seq+1,reply+1,16),packet(client,server,port,80,seq+1,reply+1,24,request),
            packet(server,client,80,port,reply+1,seq+1+len(request),24,response),
            packet(client,server,port,80,seq+1+len(request),reply+1+len(response),16)))
    with Path(path).open('wb') as stream:
        stream.write(struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,1))
        now=int(time.time())
        for i,frame in enumerate(frames):stream.write(struct.pack('<IIII',now,i*10000,len(frame),len(frame))+frame)
    return dict(method='POST',path='/api/collect',status=200,source_ip=client,destination_ip=server,decoded_artifact=expected)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output');parser.add_argument('--client',default='10.10.10.13');parser.add_argument('--server',default='10.10.10.22')
    args=parser.parse_args()
    print(json.dumps(create(args.output,args.client,args.server)))

if __name__=='__main__':main()
