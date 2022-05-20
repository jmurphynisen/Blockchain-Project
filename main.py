import hashlib
import json
from socket import SocketIO
from random import randint
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, send
from time import time
from uuid import uuid4
import random
import hmac
from Blockchain import *

"""
MAIN APP
"""
app = Flask(__name__)
socketio = SocketIO(app)

globalchain = Blockchain()
minedchain = Blockchain()
validatedchain = Blockchain()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    socketio.run(app, debug=True)

@app.route('/globalchain', methods=['GET'])
def printChain(): return globalchain 

def createCID(file):
    """
    Takes raw data as input and spits into chunks, and hashes it to create CID
    """

    chunks = chunkify(file)

    cid = hash(chunks)

    return cid

def chooseMiner(n1, n2):
    """
    Choose random miner to be n3
    Returns: index of chosen miner
    """
    miner = globalchain[randint(0, len(globalchain)-1)]
    #n3 cannot be n1 or n2
    if(n1 == miner or n2 == miner): chooseMiner(n1, n2)

    return miner['index']

@socketio.on('give_keys', namespace='/private')
def sendKeys(n1, n2, revision):
    """
    Sends keys of n1 and n2 to n3 via private message, if it is able to do that (i.e. if n1 and n2 have produced keys and are in agreement on the revision), then True
    Returns: True if both keys are present, False if otherwise
    TODO: GET SESSION IDS TO SEND MESSAGE
    """
    try: 
        message = {
            'message': 'KEY1: {}'.format(revision['authorKey']),
            'message': 'KEY2: {}'.format(revision['editorKey'])
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
    currentRevision = globalchain.revisionQueue[-1]

    n1 = currentRevision['author']
    n2 = currentRevision['editor']

    n3 = chooseMiner(n1, n2)

    if sendKeys(n1, n2, currentRevision):
        emit("New Block has been validated, ")
        validatedchain = minedchain
        #OPTIONAL: REWARD MINER

@app.route('/revisions/new', methods=['POST'])
def newRevision():
    """
    End point for adding revision to queue 
    """
    values = request.get_json()

    required = ['editor', 'author', 'file']
    for x in required:
        if x not in values:
            print('Missing values')
            return False
    cid = self.createCID(values[2])
    index = minedchain.newRevsion(values['editor'], values['author'], values['CID'])

    response = {'message': f'new revision added to queue {index}'}
    return jsonify(response), 201

@app.route('/mine', methods=['GET'])
def mine():
    """
    Creates previous hash for new block and adds it to the "mined" chain once n1 and n2 have done a joint POW
    Returns: True if new block could be added, False otherwise
    """
    currentRevision = globalchain.revisionQueue[-1]

    n1 = currentRevision['author']
    n2 = currentRevision['editor']

    proof = globalchain.proofOfWork(n1['proof'], n2['proof'])

    previousHash = globalchain.hash(globalchain.lastBlock())
    newBlock = minedchain.createBlock(proof, previousHash)
    
    if newBlock :
        print('New block has been added: ', newBlock, " proof: ", newBlock['proof'])

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
            emit(response, broadcast=True)
            globalchain = validatedchain
        else:
            response = {'message': 'Consensus has not been reached, old chain is reinstated'} 

        return jsonify(response), 200
    else:
        emit("No new chain to be added")

@app.route('nodes/register_address', methods=['POST'])
def registerAddress():
    """
    Establish endpoint so nodes can be registered using API
    """
    nodes = request.get_json().get('nodes')

    if not nodes: return "No nodes could be added", 400

    index = 0
    while index < len(nodes): globalchain.registerAddress(nodes[index])

    print("Nodes added, queue cleared")
   
