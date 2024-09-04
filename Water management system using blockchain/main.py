from blockchain import Blockchain, User
import atexit

MAX_USER_WATER_USAGE = 500  # Maximum water usage per user

def find_user(users, name):
    for user in users:
        if user.name == name:
            return user
    return None

def exit_handler(blockchain):
    blockchain.save_chain()
    print("Data saved on exit.")

def main():
    blockchain = Blockchain()
    registered_users = blockchain.users  # Load registered users from the blockchain (now as a list)
    
    # Register exit handler to save the blockchain data
    atexit.register(exit_handler, blockchain)

    while True:
        print("\n1. Register a User and Allocate Water")
        print("2. Make a Transaction")
        print("3. Mine New Block")
        print("4. View Blockchain")
        print("5. Request Water")
        print("6. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == '1':
            user_name = input("Enter the user's name: ")
            if find_user(registered_users.values(), user_name):
                print(f"User {user_name} is already registered.")
            else:
                try:
                    water_amount = float(input(f"Enter the amount of water to allocate to {user_name} (up to {MAX_USER_WATER_USAGE} units): "))
                    if water_amount > MAX_USER_WATER_USAGE or water_amount <= 0:
                        print(f"Error: You can only allocate between 1 and {MAX_USER_WATER_USAGE} units of water.")
                    else:
                        user = User(name=user_name, allocated_water=water_amount)
                        registered_users[user_name] = user
                        blockchain.users = registered_users  # Update the blockchain with the new user
                        blockchain.allocate_water(user, water_amount)
                        print(f"User {user_name} has been registered with {water_amount} units of water.")
                except ValueError:
                    print("Error: Please enter a valid number for water allocation.")
        
        elif choice == '2':
            sender_name = input("Enter sender's name: ")
            recipient_name = input("Enter recipient's name: ")
            
            sender_user = find_user(registered_users.values(), sender_name)
            recipient_user = find_user(registered_users.values(), recipient_name)
            
            if not sender_user:
                print(f"Error: Sender {sender_name} is not registered.")
            elif not recipient_user:
                print(f"Error: Recipient {recipient_name} is not registered.")
            else:
                try:
                    amount = float(input("Enter amount of water used: "))
                    purpose = input("Enter purpose of water usage (e.g., agriculture, drinking, etc.): ")
                    
                    if amount <= 0:
                        print("Error: The transaction amount must be positive.")
                    elif amount > sender_user.allocated_water:
                        print("Error: Insufficient water available for this transaction.")
                    else:
                        transaction = {
                            'sender': sender_name,
                            'recipient': recipient_name,
                            'amount': amount,
                            'purpose': purpose
                        }
                        
                        if blockchain.can_process_transactions([transaction]):
                            block = blockchain.add_block_from_user([transaction])
                            if block:
                                sender_user.allocated_water -= amount
                                recipient_user.allocated_water += amount
                                blockchain.save_chain()  # Save state after transaction
                                print("New block created and blockchain data saved.")
                        else:
                            print("Error: Insufficient water supply for the transaction.")
                
                except ValueError:
                    print("Error: Please enter a valid number for the water amount.")
        
        elif choice == '3':
            last_proof = blockchain.last_block['proof']
            proof = blockchain.proof_of_work(last_proof)
            blockchain.new_block(proof)
        
        elif choice == '4':
            for block in blockchain.chain:
                blockchain.display_block_details(block,blockchain.hash(block))
        
        elif choice == '5':
            user_name = input("Enter the user's name to request water: ")
            user = find_user(registered_users.values(), user_name)
            if not user:
                print(f"Error: User {user_name} is not registered.")
            else:
                try:
                    water_request_amount = float(input(f"Enter the amount of water {user_name} is requesting (must be {Blockchain.WATER_INCREMENT} units): "))
                    if water_request_amount != Blockchain.WATER_INCREMENT:
                        print(f"Error: You can only request exactly {Blockchain.WATER_INCREMENT} units of water.")
                    else:
                        blockchain.request_water(user_name, water_request_amount)
                        blockchain.save_chain()  # Save state after request
                except ValueError:
                    print("Error: Please enter a valid number.")
        
        elif choice == '6':
            print("Exiting the program.")
            break
        
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")

if __name__ == "__main__":
    main()
