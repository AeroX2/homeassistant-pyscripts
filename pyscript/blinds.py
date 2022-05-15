import socket
import pyscript

state.persist('pyscript.blinds_ip')
try:
    pyscript.blinds_ip
except:
    pyscript.blinds_ip = None

def find_blinds():
    if (pyscript.blinds_ip is not None):
        return pyscript.blinds_ip
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    
    s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s2.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s2.bind((local_ip, 0))
    s2.sendto(b"\xA5\xA5\xA5\xA5", ('255.255.255.255', 3311))
    
    s3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s3.settimeout(3)
    s3.bind((local_ip,3312))
    
    data, addr = s3.recvfrom(1024)
    log.info(data)
    if data == b"james_blinds_controller":
        pyscript.blinds_ip = addr[0]
        return addr[0]
    return None
    
def retry_blinds(command):
    for _ in range(3):
        try:
            blinds_ip = find_blinds()
        
            log.info("Blinds ip " + blinds_ip)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((blinds_ip, 9377))
            s.send(command)
            s.close()
            return
        except Exception as e:
            log.error(str(e))
            pyscript.blinds_ip = None
    
@service
def open_blinds():
    log.info("Open blinds")
    retry_blinds(b'U')

@service
def close_blinds():
    log.info("Close blinds")
    retry_blinds(b'D')