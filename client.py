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
        global stop_thread #global variable to stop thread in the beginning if needed
        if stop_thread: break
        try:
            message = client.recv(1024).decode('ascii') #receives message of 1024 bytes from server, decodes it
            if message == 'NICKNAME': #if the server is asking for a nickname
                client.send(nickname.encode('ascii')) #send the nickname to the server
                next_message = client.recv(1024).decode('ascii') #receives next message from the server
                if next_message == 'PASSWORD': 
                    if nickname == 'admin':
                        client.send(password.encode('ascii')) 
                    #catch the response first
                    response = client.recv(1024).decode('ascii') 
                    
                    if response == 'INCORRECT_PASSWORD': 
                        print('Connection refused! Wrong password.')
                        stop_thread = True 
                    else:
                        #if password was correct, print the welcome message
                        print(response)

                elif next_message == 'BAN': #if server sends a ban message
                    print('Connection refused! You are banned from the server.')
                    client.close()
                    stop_thread = True #stop the thread if banned
            else:
                print(message) #print message from the server
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