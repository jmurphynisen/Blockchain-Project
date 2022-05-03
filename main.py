import hashlib
import json
from socket import SocketIO
from random import randint
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, send
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

        print("New block added at ", time())

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



"""
MAIN APP
"""


app = Flask(__name__)
socketio = SocketIO(app)

blockchain = Blockchain()
minedchain = Blockchain()
validatedchain = Blockchain()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    socketio.run(app, debug=True)

@app.route('/globalchain', methods=['GET'])
def printChain(): return blockchain 

def chooseMiner(n1, n2):
    """
    Choose random miner to be n3
    Returns: index of chosen miner
    """
    miner = blockchain[randint(0, len(blockchain)-1)]
    #n3 cannot be n1 or n2
    if(n1 == miner or n2 == miner): chooseMiner(n1, n2)

    return miner['index']

@socketio.on('gives keys', namespace='/private')
def sendKeys(n1, n2, transaction):
    """
    Sends keys of n1 and n2 to n3 via private message, if it is able to do that (i.e. if n1 and n2 have produced keys and are in agreement on the transaction), then True
    Returns: True if both keys are present, False if otherwise
    TODO: GET SESSION IDS TO SEND MESSAGE
    """
    try: 
        message = {
            'message': 'KEY1: {}'.format(transaction['buyeeKey']),
            'message': 'KEY2: {}'.format(transaction['buyerKey'])
        }
        emit(message, broadcast=True)
        emit('Keys sent from ' + hash(n1) + ' and ' + hash(n2), broadcast=True)
        return True
    except:
        emit('A key was not produced', broadcast=True)
        return False

@app.route('/validate', methods=['GET'])
def validate():
    """
    Validates block by sending keys from n1 and n2 to n3
    """
    currentTransaction = blockchain.transactions[-1]

    n1 = currentTransaction['buyee']
    n2 = currentTransaction['buyer']

    n3 = chooseMiner(n1, n2)

    if sendKeys(n1, n2, currentTransaction):
        emit("New Block has been validated, ")
        validatedchain = minedchain
        #OPTIONAL: REWARD MINER

@app.route('/mine', methods=['GET'])
def mine():
    """
    Creates previous hash for new block and adds it to the "mined" chain once n1 and n2 have done a joint POW
    Returns: True if new block could be added, False otherwise
    """
    currentTransaction = blockchain.transactions[-1]

    n1 = currentTransaction['buyee']
    n2 = currentTransaction['buyer']

    proof = blockchain.POW(n1['proof'], n2['proof'])

    previousHash = blockchain.hash(blockchain.lastBlock())
    newBlock = minedchain.createBlock(proof, previousHash)
    
    if newBlock :
        print('New block has been added: ', newBlock)

    else: 
        print('New block could not be added.')
        return False

    return True      

@app.route('/verify', methods=['GET'])
def consensus():
    """
    Goes through each block in chain and has them do the proof of work with the new block, if at least 60% of them have verifiefed POW then new block is added
    Returns: global message
    """
    count = 0
    for i in range(0, len(blockchain)-1):
        block = blockchain[i]
        block2 = blockchain[-1]

        if(blockchain.POW(block, block2)):
            count += 1

    reached = (count / len(blockchain)) == .60

    if reached:
        response = {'message': 'Consensus on new block has been reached, new chain is now global chain'}
        emit(response, broadcast=True)
        blockchain = validatedchain
    else:
        response = {'message': 'Consensus has not been reached, old chain is reinstated'} 

    return jsonify(response), 200