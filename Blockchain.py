import hashlib
import json
from time import time
from uuid import uuid4
import flask
from flask import Flask, jsonify, request
import random
import hmac
from urllib.parse import urlparse
import requests
import time

from sklearn import neighbors

class Blockchain(object):
    """
    TODO: RESOLVE CONFLICTS
    """

    def __init__(self):
        """
        Initialize chain with list of nodes on network, incoming revisions and candidates, and a master chain
        """
        self.revisionQueue, self.masterChain, self.candidateQueue = [], [], []
        self.nodes = []
        self.genesis()
    
    def genesis(self): 
        """
        Create genesis block
        Returns: new block 
        """

        return self.createBlock(previousHash=1, proof=10000, cid='0000')

    def createBlock(self, proof, previousHash, cid):
        """
        Pushes new block to candidate queue, then passes it to be validated and mined by chosen third party node (n3)
        Returns: created block
        """
        newBlock = {
            'index': len(self.masterChain) + 1,
            'timestamp': time.asctime(time.localtime()),
            'revision': self.revisionQueue,
            'CID': cid,
            'proof': proof,
            'location': self.getLocation(cid),
            'previousHash': previousHash or self.hash(self.masterChain[-1]),
        }

        if previousHash == 1: self.masterChain.append(newBlock)

        self.candidateQueue.append(newBlock)

        if len(self.revisionQueue) != 0: self.revisionQueue.pop(-1)

        print("New block added at " + str(time.asctime(time.localtime())))

        return newBlock

    def generateKey():
        """
        Generates a key using 4 random digits and uses HMAC-SHA512 encoding 
        (TRY MAKING THE NODE THE SEED)
        Returns: new key 
        """
        seedArray = []
        for x in range(4): seedArray.append(random.randint(0,255))
        seed = bytearray(seedArray)
        msg = "n3 key"
        keySignature = hmac.new(seed, msg.encode(), hashlib.sha512).hexdigest()

        return keySignature

    def getLocation(self, cid):
        """
        Use file system api to retrive location by cid or whatever file is stored as 
        """
        return 0

    def newRevision(self, author, editor, cid, rawData):
        """
        Pushes new revision with editor (n2), author (n1), the location of the file, new raw data, CID, id of revision
        """
        revisionID = random.getrandbits(128)
        if editor == None:
            self.revisionQueue.append({
                'author': author,
                'editor': editor,
                'editorKey': -1,
                'authorKey': self.generateKey(),
                'CID': cid,
                'time': time.asctime(time.localtime()),
                'revisionID': revisionID,
                'rawData': hashlib.sha256(rawData)
            })
        else:
            self.revisionQueue.append({
                'author': author,
                'editor': editor,
                'editorKey': self.generateKey(),
                'authorKey': self.generateKey(),
                'CID': cid,
                'time': time.asctime(time.localtime()),
                'revisionID': revisionID,
                'rawData': hashlib.sha256(rawData)
            })

        return self.lastBlock['index'] + 1

    def lastBlock(self):
        """
        Get last block in the chain
        Returns: last block in chain
        """
        return self.masterChain[-1]

    def hash(newBlock):
        """
        Creates new hash of block
        Returns: hash of block
        """
        blockAsString = json.dumps(newBlock, sort_keys=True).encode()
        newHash = hashlib.sha256(blockAsString)

        return newHash

    def proofOfWork(self, n1proof, n2proof): #make some node
        """
        Collaborative proof of work, where both nodes n1 and n2 give some statrting proof (just some integer), and continue until proof has 4 leading 0s
        Returns: n1 and n2's proof as a tuple
        """
        while self.validateProof(n1proof, n2proof) == False:
            n1proof += 1
            n2proof += 1

        return n1proof, n2proof

    def validateProof(n1proof, n2proof):
        """
        Creates hash of n1 and n2's proof
        Returns: if 4 leading digits are 0 then True, False otherwise
        """
        hash = hashlib.sha256(str(n1proof + n2proof).encode()).hexdigest()
        return hash[:4] == '0000'
    
    def validateChain(self):
        """
        Goes through every block in chain, and checks if the previous hash is what it's supposed to be, and that the current block is in the correct place
        """
        for block in self.masterChain:
            if block['previousHash'] != self.hash(self.lastBlock()): return False
            elif self.masterChain.index(block) != self.masterChain.index(self.lastBlock()) - 1: return False

        return True
    
    def registerAddress(self, address):
        """
        Register new node on network with given address
        """
        url = urlparse(address)
        if url.netloc:
            self.nodes.append(url.netloc)
            return True
        elif url.path:
            self.nodes.append(url.path)
            return True
        else:
            print("Could not add URL")
            return False
  
    def resolveChain(self):
        """
        If at least two chains from nodes on network conflict with each other, get the most up-to-date chain (longest)
        and replace each node's chain with that one.
        """
        neighbors = self.nodes
        longestChain = None

        currentChainLength = len(self.masterChain)

        neighborsTemp = neighbors
        i = 0
        while(neighborsTemp):
            response = requests.get(f'http://{neighborsTemp[i]}/globalchain')

            if response.status_code == 200 and response.json()['length'] > currentChainLength:
                longestChain = response.json()['chain']
            
            i += 1
            neighborsTemp.pop(-1)

        if longestChain != None:
            self.masterChain = longestChain
            return True
        else: 
            return False
