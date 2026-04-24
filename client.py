import socket
import threading

nickname = input('Choose a nickname: ') #asking user for a nickname
password = "" #password variable
if nickname == 'admin':
    password = input('Enter admin password: ') #ask admin for password

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #creating a socket object for the client
client.connect(('127.0.0.1', 65535)) #connecting to the server to localhost and port 65535

stop_thread = False #variable to stop threads when needed

#function to receive messages from the server
def receive():
    while True:
        global stop_thread #using global variable to stop the thread when needed
        if stop_thread:
            break
        try:
            message = client.recv(1024).decode('ascii') #recieve message from server and decode it
            if message == 'NICKNAME': #server is asking for nickname
                client.send(nickname.encode('ascii')) #send nickname to server
                next_message = client.recv(1024).decode('ascii') #receive next message from server
                if next_message == 'PASSWORD':
                    client.send(password.encode('ascii')) #send password to server
                    if client.recv(1024).decode('ascii') == 'INCORRECT_PASSWORD': #if password is wrong server will refuse connection
                        print("Connection was refused! Wrong password!")
                        stop_thread = True #stop the thread
                elif next_message == 'BAN':
                    print('Connection refused because of ban!')
                    client.close()
                    stop_thread = True #stop the thread
                else:
                    print(next_message) #if nickname accepted, print welcome message
            else:
                print(message)
        except:
            print('An error occurred!') #print error message error and close client connection
            client.close()
            break

#function to write messages to the server
def write():
    while True:
        if stop_thread: break

        message = f'{nickname}: {input("")}' #takes input from user, formats it with the nickname

        if message[len(nickname)+2:].startswith('/'): #if the msg starts with a slash, it's a command
            if nickname == 'admin':
                if message[len(nickname)+2:].startswith('/kick'): #if the command is kick
                    client.send(f'KICK {message[len(nickname)+2+6:]}'.encode('ascii')) #send kick command to the server with the nickname to kick
                elif message[len(nickname)+2:].startswith('/ban'): #if the command is ban
                    client.send(f'BAN {message[len(nickname)+2+5:]}'.encode('ascii')) #send ban command to the server with the nickname to ban
            else:
                print('Command can only be executed by the admin!') #if not admin, print error message
        
        else: client.send(message.encode('ascii')) #send the message to the server


receive_thread = threading.Thread(target=receive) #thread for receiving messages
write_thread = threading.Thread(target=write) #thread for writing messages
receive_thread.start() #starting receive thread
write_thread.start() #starting write thread