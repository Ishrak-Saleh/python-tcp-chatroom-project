import sys
sys.path.append('..') #for parent directory imports

import socket
import threading
from config import HOST, PORT, MAX_BUFFER, APP_NAME
from database.db import init_db, is_banned
from handler import handle

init_db() #creates the db on startup

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT)) #server is bound to the localhost on point 1234567
server.listen() #server is listening for incoming connections

#list of clients and their nicknames
clients = []
nicknames = []

#function to broadcast messages to all clients
def broadcast(message):
    for client in clients:
        client.send(message) #sends the message to all clients

#function to receive incoming client connections
def receive():
    while True: #basically accepting all the connections
        client, address = server.accept() #accepts the connection, gets the client and its address
        print(f'Connected with {str(address)}') #prints the address of the client
        client.send('NICKNAME'.encode('ascii')) #asks the client for a nickname using keyword
        nickname = client.recv(MAX_BUFFER).decode('ascii') #receives the nickname from the client and decodes it

        if is_banned(nickname): #checks if nickname is banned using db function
            client.send('BAN'.encode('ascii')) #if banned, send BAN keyword to client
            client.close() #close the client connection
            continue #skip rest of the loop, wait for next connection

        if nickname == 'admin':
            client.send('PASSWORD'.encode('ascii')) #asks admin client for password using keyword
            password = client.recv(MAX_BUFFER).decode('ascii') #receives password from admin, decodes it

            if password != 'admin@123': #if password is incorrect
                client.send('INCORRECT_PASSWORD'.encode('ascii')) #sends incorrect password message to client
                client.close() #closes client connection
                continue #continue to receive next/more client connection
        
        #add nickname and client to the respective lists
        nicknames.append(nickname)
        clients.append(client)

        #print nickname on server-side, send welcome msg to client, broadcast that client has joined
        print(f'Nickname of the client is {nickname}')
        client.send(f'Welcome to {APP_NAME}, {nickname}!'.encode('ascii'))
        broadcast(f'{nickname} joined the chat!'.encode('ascii'))

        
        thread = threading.Thread(target=handle, args=(client,)) #creates one thread for each client with a handle function for handling client connection
        thread.start() #starting thread

#running the server
print('Server is listening...')
receive()