import os
import threading
import socket

host = '127.0.0.1' #localhost
port = 65535

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port)) #server is bound to the localhost on point 1234567
server.listen() #server is listening for incoming connections

#list of clients and their nicknames
clients = []
nicknames = []

#function to broadcast messages to all clients
def broadcast(message):
    for client in clients:
        client.send(message) #sends the message to all clients

#function to handle individual client connections
def handle(client):
    while True:
        try:
            message = client.recv(1024) #receives message from the client, if there is error, it means the client disconnected
            if message.decode('ascii').startswith('KICK'): #if the message starts with kick, it's a kick command
                if nicknames[clients.index(client)] == 'admin': #only admin can kick
                    name_to_kick = message.decode('ascii')[5:] #gets the nickname to kick from the message
                    kick_user(name_to_kick)
                else: client.send('Commands can only be executed by the admin!'.encode('ascii')) #if not admin, send error message

            elif message.decode('ascii').startswith('BAN'): #if the message starts with ban, it's a ban command
                if nicknames[clients.index(client)] == 'admin': #only admin can ban
                    name_to_ban = message.decode('ascii')[4:] #gets the nickname to ban from the message
                    kick_user(name_to_ban) #kick user first
                    with open('bans.txt', 'a') as f: #add the nickname to the bans.txt file (appending mode)
                        f.write(f'{name_to_ban}\n')
                    print(f'{name_to_ban} was banned!')
                else: client.send('Commands can only be executed by the admin!'.encode('ascii')) #if not admin, send error message
            else: 
                broadcast(message) #broadcasts message to all clients
        except:
            if client in clients: #if client is still in the clients list
                index = clients.index(client) #finds the index of the client in the clients list
                nickname = nicknames[index] #gets client nickname

                clients.remove(client) #removes the client from the list
                client.close() #close the client connection

                broadcast(f'{nickname} left the chat!'.encode('ascii')) #broadcasts message
                nicknames.remove(nickname) #removes the nickname from the list
                break
    
#function to receive incoming client connections
def receive():
    while True: #basically accepting all the connections
        client, address = server.accept() #accepts the connection, gets the client and its address
        print(f'Connected with {str(address)}') #prints the address of the client

        client.send('NICKNAME'.encode('ascii')) #asks the client for a nickname using keyword
        nickname = client.recv(1024).decode('ascii') #receives nickname from the client and decodes it

        #if bans.txt does not exist, create it
        if not os.path.exists('bans.txt'):
            with open('bans.txt', 'w') as f: pass

        with open('bans.txt', 'r') as f: #opens the bans.txt file in read mode
            bans = f.readlines()

        if nickname+'\n' in bans: #if the nickname is in the bans list
            client.send('BAN'.encode('ascii')) #sends ban message to the client
            client.close()
            continue #continue to receive next/more client connection

        if nickname == 'admin':
            client.send('PASSWORD'.encode('ascii')) #asks admin for password using keyword
            password = client.recv(1024).decode('ascii') #receives password from admin, decodes it

            if password != 'admin@123': #if password is incorrect
                client.send('INCORRECT_PASSWORD'.encode('ascii')) #sends incorrect password message
                client.close() #closes the client connection
                continue #continue to receive next/more client connection
                

        #appending client and nickname to the lists
        nicknames.append(nickname)
        clients.append(client)

        print(f'{client}\'s nickname is {nickname}!') #prints client nickname
        client.send('Connected to the server!'.encode('ascii')) #sends connection message to the client
        broadcast(f'{nickname} joined the chat!'.encode('ascii')) #broadcasts message every client


        thread = threading.Thread(target=handle, args=(client,)) #creates one thread for each client with a handle function to handle client connection
        thread.start() #starting thread

#function to kick a user
def kick_user(name):
    if name in nicknames: #if nickname is in the list
        name_index = nicknames.index(name) #finds index of the nickname
        client_to_kick = clients[name_index] #gets client to kick using the index

        client_to_kick.send('You were kicked by the admin!'.encode('ascii')) #sends kick message to the client
        client_to_kick.close() #closes the client connection

        clients.remove(client_to_kick) #removes client from the list
        nicknames.remove(name) #removes nickname from the list

        broadcast(f'{name} was kicked by the admin!'.encode('ascii')) #broadcast message to all clients


#running the server
print('Server is listening...')
receive()