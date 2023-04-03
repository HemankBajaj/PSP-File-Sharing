from socket import *
import threading
from constants import *

def makePORTS(size, offset, mult):
	PORTS = []
	for i in range(0, size):
		PORTS.append(i+mult*offset)
	return PORTS
clientSenderPorts = makePORTS(numClients, 10000, 1)
clientReceiverPorts =makePORTS(numClients, 11000, 1) 
serverSenderPorts =  makePORTS(numClients, 20000, 1)
serverReceiverPorts = makePORTS(numClients, 21000, 1)

def makeSOCKETS(IP_ADDR, PORTS, type):
	size = len(PORTS)
	SOCKETS = []
	for i in range(0, size):
		if type == "UDP":
			sock = socket(family=AF_INET, type=SOCK_DGRAM)
			sock.bind((IP_ADDR, PORTS[i]))
			SOCKETS.append(sock)
		elif type == "TCP":
			sock = socket(family=AF_INET, type=SOCK_STREAM)
			sock.bind((IP_ADDR, PORTS[i]))
			SOCKETS.append(sock)
	return SOCKETS
UDPSenderSockets = makeSOCKETS(SERVER_IP, serverSenderPorts, "UDP")
TCPSenderSockets = makeSOCKETS(SERVER_IP, serverSenderPorts, "TCP")
BroadcastUDP_Sockets = makeSOCKETS(SERVER_IP, serverReceiverPorts, "UDP")
TCP_ChunkReceiverSockets = makeSOCKETS(SERVER_IP, serverReceiverPorts, "TCP")

def getChunks(fileName, chunkSize):
    file = open(fileName, 'r')
    chunkID = 0; chunks = {}
    chunk = file.read(chunkSize)
    while chunk:
        chunks[chunkID] = chunk ; chunkID += 1
        chunk = file.read(chunkSize)
    file.close()
    return chunks
chunks = getChunks(FILE_NAME, BUFFER)
numChunks = len(chunks)
print(f"Server will now distribute {numChunks} chunks!")

## Cache Funtions
def makeLRU_Cache(size):
    lru = [("", -1) for i in range(size)]
    return lru
LRU_CACHE = [(-1, "") for i in range(numClients)]
def checkHit(check):
    for i in range(len(LRU_CACHE)):
        if check == LRU_CACHE[i][0]:
            LRU_CACHE.append(LRU_CACHE[i])
            data = LRU_CACHE[i][1]
            LRU_CACHE.pop(i)
            return True, data 
    return False, ""
def insertLRU(chunkID, data):
    LRU_CACHE.pop(0)      
    LRU_CACHE.append((chunkID, data))

def initList(size, obj):
	return [obj for i in range(0, size)]
connections = initList(numClients, None)
broadcastConnections = initList(numClients, None)

lock = threading.Lock()
def connectToClient(clientNum) :
    TCP_server = TCPSenderSockets[clientNum]; TCP_Broadcaster = TCP_ChunkReceiverSockets[clientNum]
    TCP_server.listen(1); conn1, addr1 = TCP_server.accept()
    connections[clientNum] = conn1
    TCP_Broadcaster.listen(1); conn2, addr2 = TCP_Broadcaster.accept()
    broadcastConnections[clientNum] = conn2
    for i in range(clientNum, TOTAL_CHUNKS, numClients):
        connections[clientNum].send(chunks[i].encode())
        ack = connections[clientNum].recv(2048).decode()
        print(f"Initial Distr : Chunk {i} sent to client {clientNum}")

threadList = []
for client in range(0, numClients):
    t = threading.Thread(target=connectToClient, args=(client,))
    threadList.append(t)
    t.start()    
for client in range(0, numClients):
    threadList[client].join()
    print(f"Initial Distr for {client} completed !")

def runServer(clientNum):
    while True:
        msg, addr = UDPSenderSockets[clientNum].recvfrom(1024); msg = msg.decode()
        TCPconn = connections[clientNum]
        if(msg == "Completed"):
            break
        chReq = int(msg)
        print(f"Chunk {chReq} requested by client {clientNum}")
        foundinCache , sendChunk = checkHit(chReq)
        if foundinCache == False:
            global lock
            with lock:
                for i in range(numClients):
                    CLIENT_ADDR = (CLIENT_IP, clientReceiverPorts[i])
                    UDP_Broadcast = BroadcastUDP_Sockets[i]; broadcast = broadcastConnections[i]
                    reqStr = str(chReq); reqStr = reqStr.encode()
                    UDP_Broadcast.sendto(reqStr, CLIENT_ADDR)
                    temp_chReq = broadcast.recv(2048).decode()
                    broadcast.send("OK".encode())
                    if temp_chReq!="NOT Found":
                        insertLRU(chReq, temp_chReq)
                        sendChunk =  temp_chReq
                        break 
        TCPconn.send(sendChunk.encode())
        TCPconn.recv(2048)       
        print(f"Chunk {chReq} sent to {clientNum} successfully")

for client in range(0, numClients):  
    x = threading.Thread(target=runServer, args=(client,))
    threadList[client] = x; x.start()
for client in range(0, numClients):
    threadList[client].join()
    print(f"File Distribution for {client} Completed")

def terminateNetwork(clientNum):
    UDPSenderSockets[clientNum].close()
    TCPSenderSockets[clientNum].close()
    TCP_ChunkReceiverSockets[clientNum].close()
    BroadcastUDP_Sockets[clientNum].close()
    connections[clientNum].close()
    broadcastConnections[clientNum].close()

print("Starting to terminate all sockets and connections.")
for client in range(0, numClients):  
    t = threading.Thread(target=terminateNetwork, args=(client,))
    threadList[client] = t; t.start()
for client in range(0, numClients):
    threadList[client].join()
print("All sockets and connections Terminated")