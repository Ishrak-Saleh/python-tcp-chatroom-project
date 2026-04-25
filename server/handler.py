#reads incoming messages from clients
#decides if it's a command or normal message
#executes commands if there are any, broadcasts normal messages to all clients

import sys
sys.path.append('..') #for parent directory imports

from server.state import clients, nicknames, broadcast, broadcast_userlist
from config import MAX_BUFFER
from server.commands import kick_user, ban_user, unban_user

#function for handling individual client connections
#runs in a separate thread for each client
def handle(client):
    while True:
        try:
            #receives message from client, decodes it, if error occurs it means client disconnected
            message = client.recv(MAX_BUFFER).decode('ascii')
            #cleaner representation of message sender
            sender = nicknames[clients.index(client)]

            #if the message starts with kick, it's a kick command
            if message.startswith('KICK'):
                if sender == 'admin':
                    name_to_kick = message[5:] #gets the nickname to kick from the message
                    kick_user(name_to_kick) #calls from commands.py to kick user

                else: client.send('You do not have permission to execute this command!'.encode('ascii')) #if not admin, send this message
            #if the message starts with ban, it's a ban command
            elif message.startswith('BAN'):
                if sender == 'admin':
                    name_to_ban = message[4:] #gets the nickname to ban from the message
                    ban_user(name_to_ban) #calls from commands.py to ban user
                else: client.send('You do not have permission to execute this command!'.encode('ascii')) #if not admin, send this message

            #if the message starts with unban, it's an unban command
            elif message.startswith('UNBAN'):
                if sender == 'admin':
                    name_to_unban = message[6:] #gets the nickname to unban from the message
                    unban_user(name_to_unban) #calls unban function from commands.py
                else:
                    client.send('You do not have permission to execute this command!'.encode('ascii')) #if not admin, send this message

            else: 
                broadcast(message.encode('ascii')) #broadcasts message to all clients


        except: 
            index = clients.index(client) #find index of client that got disconnected
            nickname = nicknames[index] #find corresponding nickname using index
            clients.remove(client) 
            client.close() 
            broadcast(f'{nickname} left the chat!'.encode('ascii')) #broadcast that client has left to all clients
            nicknames.remove(nickname) #remove nickname from nicknames list
            broadcast_userlist() #update online list for all clients
            break