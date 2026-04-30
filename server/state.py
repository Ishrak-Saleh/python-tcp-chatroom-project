#This file contains state of the server
#This will be used for keeping track of clients, their nicknames and broadcasting messages to all clients
#list of clients and their nicknames
clients = []
nicknames = []

#function to broadcast messages to all clients
def broadcast(message):
    if not message.endswith(b'\n'): #append \n if missing
        message += b'\n'
    for client in clients:
        client.send(message) #sends message in bytes to each client in clients list

#function to broadcast updated userlist to all clients
def broadcast_userlist():
    user_list = ','.join(sorted(nicknames)) #join all nicknames into a string
    for client in clients:
        try:
            client.send(f'USERLIST:{user_list}\n'.encode('ascii')) #send userlist to all clients
        except:
            pass

groups = {}

#function to broadcast a message to all members of a group
def broadcast_group(group_id, message):
    if group_id not in groups: return
    if not message.endswith(b'\n'):
        message += b'\n'
    for sock in groups[group_id]['sockets']:
        try:
            sock.send(message)
        except:
            pass

#function to get group_id for display (short hash)
def make_group_id(inviter, targets):
    import time
    raw = f'{inviter}_{",".join(sorted(targets))}_{time.time()}'
    return str(abs(hash(raw)))[:8] #8-char numeric id, ascii safe