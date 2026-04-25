#list of clients and their nicknames
clients = []
nicknames = []

#function to broadcast messages to all clients
def broadcast(message):
    for client in clients:
        client.send(message)