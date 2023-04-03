import threading
from socket import *
import hashlib
from datetime import datetime
from constants import *

def makePORTS(size, offset, mult):
	PORTS = []
	for i in range(0, size):
		PORTS.append(i+mult*offset)
	return PORTS
clientSenderPorts = makePORTS(numClients, 10000, 1)
clientReceiverPorts = makePORTS(numClients, 11000, 1) 
serverSenderPorts = makePORTS(numClients, 20000, 1)
serverReceiverPorts =  makePORTS(numClients, 21000, 1)

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
TCPSenderSocket = makeSOCKETS(CLIENT_IP, clientSenderPorts, "TCP")		
TCPReceiverSocket = makeSOCKETS(CLIENT_IP, clientReceiverPorts, "TCP")
UDPReceiverSocket = makeSOCKETS(CLIENT_IP, clientReceiverPorts, "UDP")
UDPSenderSocket = makeSOCKETS(CLIENT_IP, clientSenderPorts, "UDP")
	
def writeOnFile(fileName, text):
	file = open(fileName, 'w')
	file.write(text)
	file.close()

def initList(size, obj):
	return [obj for i in range(0, size)]
chunksReceivedClients = [{} for i in range(0, numClients)]
requiredChunksClients = [[] for i in range(0, numClients)]

## Connecting all the clients and receiving their initial chunks
def connectToServer(clientNum):
	ADDR_SENDING_PORT = (SERVER_IP, serverSenderPorts[clientNum])
	ADDR_RECVING_PORT = (SERVER_IP, serverReceiverPorts[clientNum])
	TCPReceiverSocket[clientNum].connect(ADDR_SENDING_PORT)
	TCPSenderSocket[clientNum].connect(ADDR_RECVING_PORT)
	for i in range(clientNum, TOTAL_CHUNKS, numClients):
		chunkReceived = TCPReceiverSocket[clientNum].recv(2048).decode()
		TCPReceiverSocket[clientNum].send("ReceivedOK".encode())
		chunksReceivedClients[clientNum][i] = chunkReceived
	for chunkID in range(0,TOTAL_CHUNKS):
		if chunkID not in chunksReceivedClients[clientNum].keys():
			requiredChunksClients[clientNum].append(chunkID)

threads = []
for client in range(0, numClients):
    t = threading.Thread(target = connectToServer, args=(client, ))
    threads.append(t); t.start()    
for client in range(0, numClients):
    threads[client].join()
    print(f"Connection and Initial Distribution for client {client} complete")

## PSP sharing happens here
def runClient(clientNum):
	def getMissingChunk():
		UDPSend = UDPSenderSocket[clientNum]; TCPRecv = TCPReceiverSocket[clientNum]
		SERVER_RECEIVER_ADDR = (SERVER_IP, serverSenderPorts[clientNum])
		while(len(requiredChunksClients[clientNum])>0):
			chReq = requiredChunksClients[clientNum][-1]
			requiredChunksClients[clientNum].pop()   
			UDPSend.sendto(str(chReq).encode(), SERVER_RECEIVER_ADDR)
			chunkReceived = TCPRecv.recv(2048).decode()
			TCPRecv.send("Received".encode())
			chunksReceivedClients[clientNum][chReq] = chunkReceived
    
		UDPSend.sendto("Completed".encode(), SERVER_RECEIVER_ADDR)
		if len(chunksReceivedClients[clientNum])==TOTAL_CHUNKS:
			print(f"All chunks received by client {clientNum}")
		else :
			print(f"Chunks are missing for {clientNum}")
	def sendRequestedChunk():
		while True:
			UDPRecv = UDPReceiverSocket[clientNum]; TCPSend = TCPSenderSocket[clientNum]
			chReq, addr = UDPRecv.recvfrom(1024)
			chReq = chReq.decode(); chReq = int(chReq)
			if chReq not in chunksReceivedClients[clientNum].keys():
				found = "NOT Found"
				TCPSend.send(found.encode())
			else:
				TCPSend.send(chunksReceivedClients[clientNum][chReq].encode())
			TCPSend.recv(2048)
	t1 = threading.Thread(target = getMissingChunk, args=())
	t2 = threading.Thread(target = sendRequestedChunk, args= ())
	t2.daemon = 1
	t1.start(); t2.start()
	t1.join()

	st = ""
	chunkOrder = sorted(chunksReceivedClients[clientNum].keys())
	for id in chunkOrder:
		st += chunksReceivedClients[clientNum][id]
	writeOnFile(f"CLIENT_{clientNum}", st)
	hash = hashlib.md5(st.encode()).hexdigest()
	if hash == HASH:
		print(f"Client {clientNum} received file correctly. {hash}")
	else :
		print(f"Client {clientNum} hash not match. (GOT : {hash})")

for client in range(0, numClients):   
    t = threading.Thread(target = runClient, args=(client, ))
    threads[client] = t; t.start()
for client in range(0, numClients):
    threads[client].join()
    print(f"Download Complete : Client {client}")

print("End of PSP simulation.")
endTime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
print("Ended AT =", endTime)	

