from urllib.parse import urlparse
import requests
from time import time
import json 
import hashlib

class Blockchain(object):

    def __init__(self):
        self.nodes = set()
        self.chain = []
        self.current_transactions = []

        # create the genesis block 
        self.new_block(prev_hash=1, proof=100)


    def register_node(self, address):
        """
        Add a new node to the Blockchain Network
        :param address: <str> Address of the node. E.g. 'http://192.168.0.1:5000'
        :return: None
        """ 
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)


    def new_block(self, proof, prev_hash=None):
        """
        Creates a new block and adds it to the Blockchain
        :param proof: <int> Proof given by proof of work algorith
        :param prev_hash: (Optional) <str> Hash of the previous Block
        :return: <dict> New Block 
        """  
        
        block = {
            'index' : len(self.chain) + 1,
            'timestamp' : time(),
            'transactions' : self.current_transactions,
            'proof' : proof, 
            'previous_hash' : prev_hash or self.hash(self.chain[-1])
        }

        # reset the transactions 
        self.current_transactions = []

        self.chain.append(block)
        return block

    @property
    def last_block(self):
        # returns the last block in the chain 
        return self.chain[-1]


    def new_transaction(self, sender, receiver, amount):
        """
        Creates a new transaction for the next mined Block
        :param sender: <str> Sender's Address 
        :param receiver: <str> Receiver's Address
        :param amount: <int> Transaction amount
        :return: <int> Index of the block that will hold the transaction.
        """
        
        self.current_transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount' : amount
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        """

        block_str = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_str).hexdigest()


    def proof_of_work(self, last_proof):
        """
        Simple proof of work algorithm - 
         - find a number p' such that hash(pp') contains leading 4 zeros, where p is the previous p'
         - p is the previous proof and p' is the current proof
         :param last_proof: <int> Previous proof
         :return: <int> New proof
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the proof: Does the hash(last_proof, proof) contains 4 leading zeros?
        :param last_proof: <int> Previous proof
        :param proof: <init> Current proof
        :return: <bool> True if its correct else False 
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    
    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A Blockchain
        :return: <bool> True if valid, False otherwise 
        """

        last_block = chain[0]
        current_index = 1

        # Traverse Blocks 
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print('\n-------------------\n')

            # validate hash of the block 
            if block['previous_hash'] != self.hash(last_block):
                return False

            # validate the proof of work 
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Simple Consensus Algorithm - 
        - Resolve conflicts by replacing our chain with the longest one in the network.
        :return: <bool> True if out chain was replaced, False otherwise
        """

        neighbours = self.nodes
        new_chain = None 

        # look for chains longer than ours 
        max_length = len(self.chain)

        # fetch and verify the chains from other nodes in out network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # check 
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        
        # Replace our new chain if there is eligible chain 
        if new_chain:
            self.chain = new_chain
            return True
        
        return False
