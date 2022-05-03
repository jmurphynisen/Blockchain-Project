# Blockchain-Project

**Blockchain.py**:

  - Initializes chain with gensis block and an empty transactions list, candidate queue, and "master" chain.
  Functions:
      - 'genesis(self)': Creates first block on chain with previous has 1.
      - 'createBlock(self, proof, previousHash)': creates a new instances of block, is not on chain yet but is put on candidate queue.
      - 'generateKey()': generates a unique key for a transaction that is 4 bytes long and is hashed using HMAC-SHA512 encoding.
      - 'newTransaction(self, buyer, buyee, amount)': puts new transaction with a buyer and an owner on the transactions list, 
                                                      along with the time it was made, the amount, an ID, and each of the partys' keys.
      - 'lastBlock(self)': gets the last block on the master chain.
      - 'hash(newBlock)': makes a has of some block using SHA256.
      - 'POW(self, n1proof, n2proof)': uses the guesses of two nodes to creat a proof of work for a new node n3. Guesses until valid POW is produced.
      - 'validateProof(n1proof, n2proof)': creates a hash of the guesses of n1 and n2 and if that hash's 2 leading digits are both 0 then return true.
      - 'validateChain(self)': checks integrity of chain by making sure each block has the correct previous has and that it is where it is supposed to be on the chain (right index).
 
**main.py**:
  - Utilizes Blockchain.py to initialize three chains: the global chain, a chain of mined blocks, and a chain validated blocks.
  Functions:
    - 'printChain()': creates prints each block on the chain.
    - 'chooseMiner(n1, n2)': choses a miner to mine a new block created by nodes n1 and n2.
    - 'sendKeys(n1, n2, transaction)': givben a transaction, get the keys created for n1 and n2 (owner and buyer) and send them to the chosen n3.
    - 'validate()': takes the the last transaction on the trasnaction queue and tries to validate it by checking the keys of n1 and n2 and if successful pushes that block to the validated chain.
    - 'mine()': tries to create new block from transaction between n1 and n2 and if POW is successful then it is created and added to mined chain.
    - 'consensus()': goes through nodes on global chain and have them do the POW that n1 and n2 had to do. if they all achieve the same POW and agree then block has reached consesnus and is put on global chain.
