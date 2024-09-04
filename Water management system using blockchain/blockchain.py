import hashlib
import json
import os
from time import time

class User:
    def __init__(self, name, allocated_water, request_count=0):
        self.name = name
        self.allocated_water = allocated_water
        self.request_count = request_count 

class Transaction:
    def __init__(self, sender, recipient, amount, purpose=None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.purpose = purpose

    def to_dict(self):
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'purpose': self.purpose
        }

    def validate(self):
        if not isinstance(self.sender, str) or not isinstance(self.recipient, str):
            return False
        if not isinstance(self.amount, (int, float)) or self.amount <= 0:
            return False
        return True

    def hash_transaction(self):
        tx_string = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(tx_string).hexdigest()

class Blockchain:
    MAX_WATER_SUPPLY = 10000 
    MAX_REQUESTS = 3 
    WATER_INCREMENT = 500  

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.total_water = self.MAX_WATER_SUPPLY
        self.users = {}
        self.load_chain()

    def load_chain(self):
        if os.path.exists('blockchain.json'):
            with open('blockchain.json', 'r') as file:
                data = json.load(file)
                self.chain = data.get('chain', [])
                self.current_transactions = data.get('current_transactions', [])
                self.total_water = data.get('total_water', self.MAX_WATER_SUPPLY)
                self.users = {user['name']: User(user['name'], user['allocated_water'], user.get('request_count', 0)) for user in data.get('users', [])}
        else:
            self.new_block(proof=100, previous_hash='1')

    def save_chain(self):
        with open('blockchain.json', 'w') as file:
            json.dump({
                'chain': self.chain,
                'current_transactions': self.current_transactions,
                'total_water': self.total_water,
                'users': [vars(user) for user in self.users.values()]
            }, file, indent=4)

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]) if self.chain else '1',
        }
        block_hash = self.hash(block)
        self.current_transactions = []
        self.chain.append(block)
        self.save_chain()
        self.display_block_details(block, block_hash)
        return block

    def add_block_from_user(self, transactions):
        try:
            validated_transactions = []
            for tx in transactions:
                transaction = Transaction(tx['sender'], tx['recipient'], tx['amount'], tx.get('purpose'))
                if transaction.validate():
                    validated_transactions.append(tx)
                else:
                    raise ValueError("Invalid transaction details in user input.")
            if not self.can_process_transactions(validated_transactions):
                raise ValueError("Not enough water in total supply to process these transactions.")

            last_proof = self.last_block['proof']
            proof = self.proof_of_work(last_proof)
            previous_hash = self.hash(self.chain[-1])
            
            block = {
                'index': len(self.chain) + 1,
                'timestamp': time(),
                'transactions': validated_transactions,
                'proof': proof,
                'previous_hash': previous_hash,
            }
            block_hash = self.hash(block)
            self.chain.append(block)
            self.update_user_allocations(validated_transactions)
            
            self.save_chain()
            
            self.display_block_details(block, block_hash)
            
            return block

        except ValueError as e:
            print(f"Error: {e}")
            return None


    def update_user_allocations(self, transactions):
        for tx in transactions:
            sender = self.users.get(tx['sender'])
            recipient = self.users.get(tx['recipient'])

            if sender and recipient:
                if sender.allocated_water >= tx['amount']:
                    sender.allocated_water -= tx['amount']
                    recipient.allocated_water += tx['amount']
                else:
                    print(f"Error: {sender.name} does not have enough allocated water for this transaction.")
            else:
                print(f"Error: Either the sender or recipient does not exist in the system.")

    def can_process_transactions(self, transactions):
        total_amount = sum(tx['amount'] for tx in transactions)
        if total_amount > self.total_water:
            return False
        for tx in transactions:
            sender = self.users[tx['sender']]
            if sender.allocated_water < tx['amount']:
                return False
        return True

    def allocate_water(self, user, amount):
        if amount <= self.total_water:
            self.total_water -= amount
            return True
        return False

    def new_transaction(self, sender, recipient, amount, purpose=None):
        if amount > self.total_water:
            raise ValueError("Not enough water available for this transaction.")
        transaction = Transaction(sender, recipient, amount, purpose)
        if transaction.validate():
            transaction_hash = transaction.hash_transaction()
            self.current_transactions.append(transaction.to_dict())
            self.save_chain()  
            print(f"Transaction created. Hash: {transaction_hash}")
            return self.last_block['index'] + 1
        else:
            raise ValueError("Invalid transaction details.")

    def request_water(self, user_name, request_amount):
        if request_amount != self.WATER_INCREMENT:
            raise ValueError(f"Request amount must be exactly {self.WATER_INCREMENT} units.")
        if user_name not in self.users:
            raise ValueError("User not registered.")
        
        user = self.users[user_name]
        if user.request_count >= self.MAX_REQUESTS:
            raise ValueError(f"User {user_name} has already made the maximum number of requests.")
        if self.total_water < request_amount:
            raise ValueError("Not enough water available for this request.")
        
        user.allocated_water += request_amount
        user.request_count += 1
        self.total_water -= request_amount
        self.save_chain()  # Save after request
        print(f"{request_amount} units of water have been allocated to {user_name}.")

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def validate_chain(self):
        last_block = self.chain[0]
        for block in self.chain[1:]:
            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            for tx in block['transactions']:
                transaction = Transaction(tx['sender'], tx['recipient'], tx['amount'], tx.get('purpose'))
                if not transaction.validate():
                    return False
            last_block = block
        return True

    def update_water_supply(self, transactions=None):
        if transactions is None:
            transactions = self.current_transactions
        for tx in transactions:
            self.total_water -= tx['amount']

    def display_block_details(self, block, block_hash):
        print(f"\nBlock {block['index']} created at {block['timestamp']}")
        print(f"Block Hash: {block_hash}")
        print("Transactions:")
        for tx in block['transactions']:
            print(f"  - {tx['sender']} sent {tx['amount']} units of water to {tx['recipient']}. Purpose: {tx['purpose']}")
        print(f"Remaining Government Water Supply: {self.total_water} units")
