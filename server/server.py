import sys
import random
sys.path.append('..') #for parent directory imports

import socket
import threading
from config import HOST, PORT, MAX_BUFFER, APP_NAME
from database.db import init_db, is_banned, get_recent_messages
from server.state import clients, nicknames, broadcast, broadcast_userlist

init_db() #creates the db on startup

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#function to assign unique nickname if nickname already exists
def assign_nickname(requested_name):
    while True:
        candidate = f"{requested_name}_{random.randint(1000, 9999)}" #append random 4 digit number
        if candidate not in nicknames: #check if candidate nickname is unique
            return candidate

#function to receive incoming client connections
def receive():
    from server.handler import handle #importing here to avoid circular imports
    while True: #basically accepting all the connections
        client, address = server.accept() #accepts the connection, gets the client and its address
        print(f'Connected with {str(address)}') #prints the address of the client
        client.send('NICKNAME'.encode('ascii')) #asks the client for a nickname using keyword
        nickname = client.recv(MAX_BUFFER).decode('ascii') #receives the nickname from the client and decodes it

        if is_banned(nickname): #check if the nickname is banned using db function
            client.send('BAN'.encode('ascii')) #send BAN keyword to client if banned
            #close client connection and skip rest of loop, wait for next connection
            client.close()
            continue

        if nickname == 'admin':
            if 'admin' in nicknames: #block second admin session
                client.send('ADMIN_ALREADY_CONNECTED'.encode('ascii'))
                client.close()
                continue

            client.send('PASSWORD'.encode('ascii')) #ask admin client for password using keyword
            password = client.recv(MAX_BUFFER).decode('ascii') #recieve password from admin and decodes it

            if password != 'admin@123': #if incorrect admin password (hardcoded for now)
                client.send('INCORRECT_PASSWORD'.encode('ascii')) #send incorrect password message to client
                client.close()
                continue

        if nickname != 'admin':
            nickname = assign_nickname(nickname) #assign unique nickname number
        client.send(f'ASSIGNED_NICKNAME:{nickname}'.encode('ascii')) #tell client their assigned nickname

        #add client and nickname to list
        nicknames.append(nickname)
        clients.append(client)

        #print nickname of client connected to server (debugging)
        print(f'Nickname of the client is {nickname}')
        client.send(f'Welcome to {APP_NAME}, {nickname}!'.encode('ascii'))

        history = get_recent_messages('general') #get recent messages from general channel using db function
        if history: 
            client.send('[SYS] --- message history ---\n'.encode('ascii'))
            for sender, message, timestamp in history:
                t = timestamp[11:16]  # extract HH:MM from sqlite datetime
                client.send(f'[{t}] {sender}: {message}\n'.encode('ascii'))
            client.send('[SYS] --- live session ---\n'.encode('ascii'))

        broadcast(f'{nickname} joined the chat!'.encode('ascii'))
        broadcast_userlist() #update online list for all clients

        thread = threading.Thread(target=handle, args=(client,)) #creates one thread for each client with a handle function for handling client connection
        thread.start() #starting thread

#function to start the server
def start():
    server.bind((HOST, PORT)) #server is bound to the localhost on point 1234567
    server.listen() #server is listening for incoming connections
    print('Server is listening...')
    receive() #call recieve function to start accepting clients

if __name__ == '__main__':
    start()