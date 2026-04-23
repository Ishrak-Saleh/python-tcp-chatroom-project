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
            message = client.recv(1024) #receives message of 1024 bytes from the client
            broadcast(message) #broadcasts message to all clients
        except:
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

        #appending client and nickname to the lists
        nicknames.append(nickname)
        clients.append(client)

        print(f'{client}\'s nickname is {nickname}!') #prints client nickname
        broadcast(f'{nickname} joined the chat!'.encode('ascii')) #broadcasts message every client
        client.send('Connected to the server!'.encode('ascii')) #sends connection message to the client

        thread = threading.Thread(target=handle, args=(client,)) #creates one thread for each client with a handle function to handle client connection
        thread.start() #starting thread


#running the server
print('Server is listening...')
receive()