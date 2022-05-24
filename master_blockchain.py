import hashlib
import json
from multiprocessing.sharedctypes import Value
from time import time
from uuid import uuid4
from argparse import ArgumentParser
from attr import has
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, send
import random
import hmac
from urllib.parse import urlparse
import requests
import time
from random import randint

class Blockchain(object):
    """
    TODO: RESOLVE CONFLICTS
    """

    def __init__(self):
        """
        Initialize chain with list of nodes on network, incoming revisions and candidates, and a master chain
        """
        self.revisionQueue, self.masterChain = [], []
        self.nodes = []
        self.genesis()
        #self.newRevision(author=None, editor=None, cid='0000', rawData=1234)
        #self.proofOfWork(1)
    
    def genesis(self): 
        """
        Create genesis block
        Returns: new block 
        """

        return self.createBlock(previousHash=1, proof=10000, cid='0000', author=None)

    def createBlock(self, proof, previousHash, cid, author, revisionId=None):
        """
        Pushes new block to candidate queue, then passes it to be validated and mined by chosen third party node (n3)
        Returns: created block
        """
        if previousHash == 1: 
            newBlock = {
                    'index': len(self.masterChain) + 1,
                    'timestamp': time.asctime(time.localtime()),
                    'author': author,
                    'CID': cid,
                    'proof': proof,
                    'revisionID': revisionId,
                    'location': self.getLocation(cid),
                    'previousHash': previousHash,
            }
            self.masterChain.append(newBlock)
            print("New block added at " + str(time.asctime(time.localtime())))
            return newBlock
        else: 
            newBlock = {
                'index': len(self.masterChain) + 1,
                'timestamp': time.asctime(time.localtime()),
                'author': author,
                'CID': cid,
                'proof': proof,
                'revisionID': revisionId,
                'location': self.getLocation(cid),
                'previousHash': previousHash,
            }
            self.masterChain.append(newBlock)
            print("New block added at " + str(time.asctime(time.localtime())))
            return newBlock
    
        print('Could not add new block')
        return 0

    def generateKey(self):
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
        revisionID = random.getrandbits(64)
        if editor == None:
            self.revisionQueue.append({
                'author': author,
                'editor': editor,
                'editorKey': -1,
                'authorKey': self.generateKey(),
                'CID': cid,
                'time': time.asctime(time.localtime()),
                'revisionID': revisionID,
                'rawData': self.hash(rawData)
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
                'rawData': self.hash(rawData)
            })

        lastBlock = self.lastBlock()
        return lastBlock['index'] + 1

    def lastBlock(self):
        """
        Get last block in the chain
        Returns: last block in chain
        """
        return self.masterChain[-1]

    def hash(self, newBlock):
        """
        Creates new hash of block
        Returns: hash of block
        """
        blockAsString = json.dumps(newBlock, sort_keys=True).encode()
        newHash = hashlib.sha256(blockAsString)

        return newHash

    def proofOfWork(self, proof): #make some node
        """
        Collaborative proof of work, where both nodes n1 and n2 give some statrting proof (just some integer), and continue until proof has 4 leading 0s
        Returns: n1 and n2's proof as a tuple
        """
        while not self.validateProof(proof): proof += 1
        return proof

    def validateProof(self, proof):
        """
        Creates hash of n1 and n2's proof
        Returns: if 4 leading digits are 0 then True, False otherwise
        """
        hash = hashlib.sha256(str(proof).encode()).hexdigest()
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
        elif url.path:
            self.nodes.append(url.path)
        else:
            response = {'message': 'Could not parse URL'}
            return jsonify(response), 400
  
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

            neighborsTemp.pop(i)
            i += 1
            

        if longestChain != None:
            self.masterChain = longestChain
            return True
        else: 
            return False

"""
MAIN APP
"""
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
node_identifier = str(uuid4()).replace('-', '')

pastRevisions = []
globalchain = Blockchain()
minedchain = Blockchain()
validatedchain = Blockchain()


def replaceValidatedChain(chain):
    validatedchain = chain
    return 0
def getGlobalChain(): return globalchain
def setGlobalChain(chain): 
    globalchain = chain
    return 0
@app.route('/globalchain', methods=['GET'])
def printChain(): 
    response = {
        'chain': globalchain.masterChain,
        'length': len(globalchain.masterChain)
    }
    return jsonify(response), 200

def createCID(file):
    """
    Takes raw data as input and spits into chunks, and hashes it to create CID
    
    chunks = chunkify(file)

    cid = hash(chunks)

    return cid
    """
    response = {'message': 'still work in progress'}
    return jsonify(response), 400

def chooseMiner(n1, n2):
    """
    Choose random miner to be n3
    Returns: index of chosen miner
    """
    miner = globalchain.nodes[randint(0, len(globalchain)-1)]

    #n3 cannot be n1 or n2
    if(n1 == miner or n2 == miner): chooseMiner(n1, n2)

    return miner

@app.route('/give_keys', methods=['GET'])
def sendKeys(n1, n2, revision):
    """
    Sends keys of n1 and n2 to n3 via private message, if it is able to do that (i.e. if n1 and n2 have produced keys and are in agreement on the revision), then True
    Returns: True if both keys are present, False if otherwise
    TODO: GET SESSION IDS TO SEND MESSAGE
    """
    try: 
        message = {
            'message': 'KEY1: {}'.format(revision['authorKey']),
            'message1': 'KEY2: {}'.format(revision['editorKey'])
        }
        #emit(message, broadcast=True)
        #emit('Keys sent from ' + hash(n1) + ' and ' + hash(n2), broadcast=True)
        return jsonify(message), 200
    except:
        raise ValueError("Keys could not be produced")

@app.route('/validate', methods=['GET'])
def validate():
    """
    Validates block by sending keys from n1 and n2 to n3
    """
    currentblock = minedchain.lastBlock()
    print(pastRevisions)
    for revision in pastRevisions:
        if revision['revisionID'] == currentblock['revisionID']:
            currentRevision = revision
            break
        return 'No blocks to validate!', 400
    
    n1 = currentRevision['author']
    n2 = currentRevision['editor']

    if sendKeys(n1, n2, currentRevision):
        validatedchain.masterChain = minedchain.masterChain
        hashBlock = hash(currentblock['CID'])

        response = {'message': 'New block: ' + str(hashBlock) + ' has been validated'}
        return jsonify(response) , 200
        #OPTIONAL: REWARD MINER

@app.route('/revisions/new', methods=['POST'])
def newRevision():
    """
    End point for adding revision to queue 
    """
    values = request.get_json()
    minedchain.newRevision(editor=None, author=None, cid='0000', rawData=1234)
    print(minedchain.revisionQueue)
    required = ['editor', 'author', 'file']
    for x in required:
        if x not in values:
            response = {'message': 'must have all values'}
            return jsonify(response), 400
    cid = createCID(values[2])
    index = minedchain.newRevision(values['editor'], values['author'], cid, rawData=values['file'])

    response = {'message': f'new revision added to queue {index}'}
    return jsonify(response), 201

@app.route('/mine', methods=['GET'])
def mine():
    """
    Creates previous hash for new block and adds it to the "mined" chain once n1 and n2 have done a joint POW
    Returns: True if new block could be added, False otherwise
    """
    currentblock = minedchain.lastBlock()
    for revision in minedchain.revisionQueue:
        if revision['CID'] == currentblock['CID']:
            currentRevision = revision
            minedchain.revisionQueue.remove(revision)
            pastRevisions.append(revision)
            break

    #special case for when proposing revision to genesis block
    n1 = currentblock['author']
    n2 = currentRevision['editor']
    if n1 != None and n2 != None:
        n3 = chooseMiner(n1, n2)
        proof = globalchain.proofOfWork(n3['proof'])
    else:
        proof = globalchain.proofOfWork(currentblock['proof'])

    previousHash = globalchain.hash(globalchain.lastBlock())
    newBlock = minedchain.createBlock(proof=proof, previousHash=previousHash, cid=currentRevision['CID'], author=currentblock['author'], revisionId=currentRevision['revisionID'])
    
    if newBlock :
        response = {
            'message': "File overwritten",
            'CID': newBlock['CID'],
            'index': newBlock['index'],
            'revisionID': newBlock['revisionID'],
            'proof': newBlock['proof'],
        }
        return jsonify(response), 200

    else: 
        response = {'message':'New block could not be added.'}
        return jsonify(response), 400     

@app.route('/nodes/consensus', methods=['GET'])
def consensus():
    """
    Goes through each block in chain and has them do the proof of work with the new block, if at least 60% of them have a chain longer than the current one then new block is added
    Returns: global message
    """

    chain = getGlobalChain()

    currentChainLength = len(chain.masterChain)

    chains = []
    nodes = chain.nodes
    i = 0
    while(nodes):
        response = requests.get(f'http://{nodes[i]}/globalchain')

        if response.status_code == 200 and response.json()['length'] > currentChainLength:
            chains.append(response.json()['chain'])
        
        nodes.pop(i)
        i += 1

    if len(chains) / len(chain.nodes) >= .60:
        response = {'message': 'Consensus on new block has been reached, new chain is now global chain'}
        setGlobalChain(validatedchain)
        return jsonify(response), 200
    else: 
        response = {'message': 'Consensus has not been reached, old chain is reinstated'} 
        return jsonify(response), 400

    """
    x
    if len(validatedchain) > len(globalchain):
        count = 0
        for i in range(0, len(globalchain)-1):
            block = globalchain[i]
            block2 = globalchain[-1]
            if(globalchain.proofOfWork(block, block2)):
                count += 1
        reached = (count / len(globalchain)) == .60
        if reached:
            response = {'message': 'Consensus on new block has been reached, new chain is now global chain'}
            globalchain = validatedchain
        else:
            response = {'message': 'Consensus has not been reached, old chain is reinstated'} 
        return jsonify(response), 200
    else:
        emit("No new chain to be added")
    """

@app.route('/nodes/register_address', methods=['POST'])
def registerAddress():
    """
    Establish endpoint so nodes can be registered using API
    """
    nodes = request.get_json().get('nodes')

    if not nodes: 
        response = {'message': 'Nodes could not be added'}
        return jsonify(response), 200

    index = 0
    while index < len(nodes): globalchain.registerAddress(nodes[index])

    response = {'message': 'Nodes added, queue cleared'}
    return jsonify(response), 200

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)
