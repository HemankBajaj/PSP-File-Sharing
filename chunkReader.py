## This function is used in constants.py
def getTotalChunks(fileName, chunkSize):
    file = open(fileName, 'r')
    chunkID = 0; chunks = {}
    chunk = file.read(chunkSize)
    while chunk:
        chunks[chunkID] = chunk ; chunkID += 1
        chunk = file.read(chunkSize)
    file.close()
    return len(chunks)
