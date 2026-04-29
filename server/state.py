#This file contains state of the server
#This will be used for keeping track of clients, their nicknames and broadcasting messages to all clients
#list of clients and their nicknames
clients = []
nicknames = []

#function to broadcast messages to all clients
def broadcast(message):
    for client in clients:
        client.send(message) #sends message in bytes to each client in clients list

#function to broadcast updated userlist to all clients
def broadcast_userlist():
    user_list = ','.join(sorted(nicknames)) #join all nicknames into a string
    for client in clients:
        try:
            client.send(f'\nUSERLIST:{user_list}'.encode('ascii')) #send userlist to all clients
        except:
            pass