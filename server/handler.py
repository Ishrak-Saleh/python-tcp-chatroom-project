#reads incoming messages from clients
#decides if it's a command or normal message
#executes commands if there are any, broadcasts normal messages to all clients

import sys
sys.path.append('..') #for parent directory imports

from datetime import datetime
from server.state import clients, nicknames, broadcast, broadcast_userlist
from config import MAX_BUFFER
from server.commands import kick_user, ban_user, unban_user
from database.db import log_message

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
                else: client.send('You do not have permission to execute this command!'.encode('ascii'))

            #if the message starts with unban, it's an unban command
            elif message.startswith('UNBAN'):
                if sender == 'admin':
                    name_to_unban = message[6:] #gets the nickname to unban from the message
                    unban_user(name_to_unban) #calls unban function from commands.py
                else:
                    client.send('You do not have permission to execute this command!'.encode('ascii'))

            #if the mssage starts with banlist, it's a banlist
            elif message.startswith('BANLIST'):
                if sender == 'admin':
                    from database.db import get_banned_list
                    banned = get_banned_list()
                    if banned:
                        result = '[SYS] Banned users: ' + ', '.join(banned)
                    else:
                        result = '[SYS] No banned users.'
                    client.send(f'{result}\n'.encode('ascii')) #send only to admin
                else:
                    client.send('You do not have permission to execute this command!\n'.encode('ascii'))

            
            #if the message starts with ban, it's a ban command
            elif message.startswith('BAN'):
                if sender == 'admin':
                    name_to_ban = message[4:] #gets the nickname to ban from the message
                    ban_user(name_to_ban) #calls from commands.py to ban user
                else: client.send('You do not have permission to execute this command!'.encode('ascii'))
            
            #if the message starts with dm, it's a dm command
            elif message.startswith('DM '): #handle direct message command
                parts = message[3:].split(' ', 1) #split into target nickname and message body
                if len(parts) == 2:
                    target, dm_msg = parts
                    if target in nicknames: #check if target user is online
                        target_client = clients[nicknames.index(target)] #find target client socket
                        target_client.send(f'[DM from {sender}] {dm_msg}\n'.encode('ascii')) #send to receiver
                        client.send(f'[DM to {target}] {dm_msg}\n'.encode('ascii')) #confirm to sender
                    else:
                        client.send(f'[SYS] User "{target}" not found.\n'.encode('ascii')) #user offline or wrong name

            else:
                timestamp = datetime.now().strftime('%H:%M') #get current time in HH:MM format
                broadcast(f'[{timestamp}] {message}'.encode('ascii')) #broadcast message with timestamp prefix

                #log message to database, extract actual message by splitting, if format is [HH:MM] sender: message, else log whole message
                log_message(sender, 'general', message.split(': ', 1)[1] if ': ' in message else message) 

        except:
            index = clients.index(client) #find index of client that got disconnected
            nickname = nicknames[index] #find corresponding nickname using index
            clients.remove(client)
            client.close()
            broadcast(f'{nickname} left the chat!'.encode('ascii')) #broadcast that client has left
            nicknames.remove(nickname)
            broadcast_userlist() #update online list after user leaves
            break