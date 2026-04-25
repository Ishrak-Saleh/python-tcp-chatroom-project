#list of clients and their nicknames
clients = []
nicknames = []


def broadcast(message):
    for client in clients:
        client.send(message)