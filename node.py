from flask.wrappers import Response
import requests
from blockchain import Blockchain
from flask import Flask, jsonify, request
from uuid import uuid4

app = Flask(__name__, instance_relative_config=True)

# Generate a unique address for this node 
node_id = str(uuid4()).replace('-', '')

# Instantiate the blockchain 
blockchain = Blockchain()

## Blockchain Network ##

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Invalid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message' : 'New nodes have been added',
        'total_nodes' : list(blockchain.nodes)
    }

    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message' : 'Our chain was replaced',
            'new_chain' : blockchain.chain
        }
    else:
        response = {
            'message' : 'Our chain is authoritative',
            'chain' : blockchain.chain
        }

    return jsonify(response), 200

## Blockchain Activities ##

@app.route('/mine', methods=['GET'])
def mine():
    
    # proof of work 
    last_block = blockchain.last_block
    prev_proof = last_block['proof']
    proof = blockchain.proof_of_work(prev_proof)

    # receive a reward for finding proof
    blockchain.new_transaction(
        sender="block-mining-rewarder",
        receiver=node_id,
        amount=1
    ) 

    # forge the new block and add it to blockchain 
    prev_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, prev_hash)

    response = {
        'message' : "New Block Forged",
        'index' : block['index'],
        'transactions' : block['transactions'],
        'proof' : block['proof'],
        'previous_hash' : block['previous_hash']
    }

    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def get_chain():
    response = {
        'chain' : blockchain.chain,
        'length' : len(blockchain.chain)
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # request validation 
    required = ['sender', 'receiver', 'amount']
    if not all(key in values for key in required):
        return 'Missing values', 400

    # create a new transaction
    index = blockchain.new_transaction(values['sender'], values['receiver'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'} 
    return jsonify(response), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
