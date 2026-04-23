import socket
import threading

nickname = input('Choose a nickname: ') #asking user for a nickname

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #creating a socket object for the client
client.connect(('127.0.0.1', 65535)) #connecting to the server to localhost and port 65535

#function to receive messages from the server
def receive():
    while True:
        try:
            message = client.recv(1024).decode('ascii') #receives message of 1024 bytes from server, decodes it
            if message == 'NICKNAME': #if the server is asking for a nickname
                client.send(nickname.encode('ascii')) #send the nickname to the server
            else:
                print(message) #print message from the server
        except:
            print('An error occurred!') #print error message error and close client connection
            client.close()
            break

#function to write messages to the server
def write():
    while True:
        message = f'{nickname}: {input("")}' #takes input from user, formats it with the nickname
        client.send(message.encode('ascii')) #sends message to the server


receive_thread = threading.Thread(target=receive) #thread for receiving messages
write_thread = threading.Thread(target=write) #thread for writing messages
receive_thread.start() #starting receive thread
write_thread.start() #starting write thread