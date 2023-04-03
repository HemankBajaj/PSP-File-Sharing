import hashlib
from chunkReader import *
## NUMBER OF CLIENTS 
numClients = 5
## FILE SPECIFIC INFO 
FILE_NAME = "A2_small_file.txt"
## SET BUFFER SIZE
BUFFER = 1024


TOTAL_CHUNKS = getTotalChunks(FILE_NAME, BUFFER)
# HASH = "131408ce72342729942748186d94d814"
fileContents = open(FILE_NAME, 'r').read()
HASH = hashlib.md5(fileContents.encode()).hexdigest()

## CONSTANTS
SERVER_IP = "127.0.0.1"
CLIENT_IP = "127.0.0.1"
