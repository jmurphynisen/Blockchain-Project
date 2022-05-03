import hashlib
import json
from time import time
from uuid import uuid4
import flask
from flask import Flask, jsonify, request
import random
import hmac

class Blockchain(object):
    """
    TODO: RESOLVE CONFLICTS
    """

    def __init__(self):
        """
        Initialize chain with list of incoming transactions, a global chain, and a queue of candidate blocks to be validated
        """
        self.transactions, self.masterChain, self.candidateQueue = [], [], []
        self.minedchain = []
        self.genesis()
    
    def genesis(self): 
        """
        Create genesis block
        Returns: new block 
        """
        return self.createBlock(previousHash=1, proof=10000)

    def createBlock(self, proof, previousHash):
        """
        Pushes new block to candidate queue, then passes it to be validated and mined by chosen third party node (n3)
        Returns: created block
        """
        newBlock = {
            'index': len(self.masterChain) + 1,
            'timestamp': time(),
            'transactions': self.transactions,
            'proof': proof,
            'previousHash': previousHash or self.hash(self.chain[-1]),
        }

        if previousHash == 1: self.masterChain.append(newBlock)

        self.candidateQueue.append(newBlock)

        if len(self.transactions) != 0: self.transactions.pop(-1)

        print("New block added at " + time())

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

    def newTransaction(self, buyer, buyee, amount):
        """
        Pushes new transaction with buyer (n2), buyee (n1), the amount the book sold for, time it was made, and an ID for the transaction
        """
        transID = random.getrandbits(128)
        self.transactions.append({
            'buyer': buyer,
            'buyee': buyee,
            'buyerKey': self.generateKey(),
            'buyeeKey': self.generateKey(),
            'amount': amount,
            'time': time(),
            'transID': transID
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

    def POW(self, n1proof, n2proof): #make some node
        """
        Collaborative proof of work, where both nodes n1 and n2 give some statrting proof (just some integer), and continue until proof has 4 leading 0s
        Returns: n1 and n2's proof as a tuple
        """
        while self.validateProof(n1proof, n2proof) is False:
            n1proof += 1
            n2proof += 1

        return n1proof, n2proof

    def validateProof(n1proof, n2proof):
        """
        Creates hash of n1 and n2's proof
        Returns: if 2 leading digits are 0 then True, False otherwise
        """
        hash = hashlib.sha256(str(n1proof + n2proof).encode()).hexdigest()
        return hash[:4] == '00'
    
    def validateChain(self):
        """
        Goes through every block in chain, and checks if the previous hash is what it's supposed to be, and that the current block is in the correct place
        """
        for block in self.masterChain:
            if block['previousHash'] != self.hash(self.lastBlock()): return False
            elif self.masterChain.index(block) != self.masterChain.index(self.lastBlock()) - 1: return False

        return True