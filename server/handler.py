#reads incoming messages from clients
#decides if it's a command or normal message
#executes commands if there are any, broadcasts normal messages to all clients

import sys
import time
sys.path.append('..') #for parent directory imports

from datetime import datetime
from server.state import clients, nicknames, broadcast, broadcast_userlist
from config import MAX_BUFFER
from server.commands import kick_user, ban_user, unban_user, group_invite, group_accept, group_leave, group_send
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
                    targets = [n.strip() for n in message[5:].split(',')] #get all the nicknames to kick from the message
                    targets_to_kick = [(n, clients[nicknames.index(n)]) for n in targets if n in nicknames] #snapshot name+socket pairs before any removals
                    for name, sock in targets_to_kick: #send kick message to all targets first
                        sock.send('You have been kicked from the server!\n'.encode('ascii'))
                    time.sleep(0.05) #small delay to let messages flush before sockets close
                    for name, _ in targets_to_kick: #now remove each target from the server
                        if name in nicknames: #guard against race conditions
                            kick_user(name)
                else:
                    client.send('You do not have permission to execute this command!\n'.encode('ascii'))

            #if the message starts with unban, it's an unban command
            elif message.startswith('UNBAN'):
                if sender == 'admin':
                    for name in [n.strip() for n in message[6:].split(',')]: #get all the nicknames to unban from the message
                        unban_user(name) #calls unban function from commands.py
                else:
                    client.send('You do not have permission to execute this command!\n'.encode('ascii'))

            #if the message starts with banlist, it's a banlist command
            elif message.startswith('BANLIST'):
                if sender == 'admin':
                    from database.db import get_banned_list
                    banned = get_banned_list() #fetch list of banned users from database
                    if banned:
                        result = '[SYS] Banned users: ' + ', '.join(banned) #format list into readable string
                    else:
                        result = '[SYS] No banned users.'
                    client.send(f'{result}\n'.encode('ascii')) #send banlist only to admin
                else:
                    client.send('You do not have permission to execute this command!\n'.encode('ascii'))

            #if the message starts with ban, it's a ban command
            elif message.startswith('BAN'):
                if sender == 'admin':
                    targets = [n.strip() for n in message[4:].split(',')] #get all the nicknames to ban from the message
                    targets_to_ban = [(n, clients[nicknames.index(n)]) for n in targets if n in nicknames and n != 'admin'] #snapshot name+socket pairs, exclude admin
                    for name, sock in targets_to_ban: #send ban message to all targets first
                        sock.send('You have been banned from the server!\n'.encode('ascii'))
                    time.sleep(0.05) #small delay to let messages flush before sockets close
                    for name, _ in targets_to_ban: #now remove and ban each target
                        if name in nicknames: #guard against race conditions
                            ban_user(name)
                else:
                    client.send('You do not have permission to execute this command!\n'.encode('ascii'))

            #if the message starts with dm, it's a direct message command
            elif message.startswith('DM '):
                parts = message[3:].split(' ', 1) #split into target nickname and message body
                if len(parts) == 2:
                    target, dm_msg = parts
                    if target in nicknames: #check if target user is online
                        target_client = clients[nicknames.index(target)] #find target client socket
                        target_client.send(f'[DM from {sender}] {dm_msg}\n'.encode('ascii')) #send dm to receiver
                        client.send(f'[DM to {target}] {dm_msg}\n'.encode('ascii')) #send confirmation to sender
                    else:
                        client.send(f'[SYS] User "{target}" not found.\n'.encode('ascii')) #user offline or wrong name

            #if message starts with GROUP_INVITE, user wants to create a group
            elif message.startswith('GROUP_INVITE '):
                targets = [t.strip() for t in message[13:].split(',')]
                group_invite(sender, targets)

            #if message starts with GROUP_ACCEPT, user accepted a group invite
            elif message.startswith('GROUP_ACCEPT '):
                group_id = message[13:].strip()
                group_accept(group_id, sender)

            #if message starts with GROUP_DECLINE, user declined invite
            elif message.startswith('GROUP_DECLINE '):
                group_id = message[14:].strip()
                #notify group members that user declined
                from server.state import groups, broadcast_group
                if group_id in groups:
                    broadcast_group(group_id, f'GROUP_MSG {group_id} [SYS] {sender} declined the invite.'.encode('ascii'))

            #if message starts with GROUP_SEND, relay message to group
            elif message.startswith('GROUP_SEND '):
                parts = message[11:].split(' ', 1)
                if len(parts) == 2:
                    group_send(parts[0], sender, parts[1])

            #if message starts with GROUP_LEAVE, remove user from group
            elif message.startswith('GROUP_LEAVE '):
                group_id = message[12:].strip()
                group_leave(group_id, sender)

            #otherwise it's a normal chat message, broadcast to everyone
            else:
                timestamp = datetime.now().strftime('%H:%M') #get current time in HH:MM format
                broadcast(f'[{timestamp}] {message}'.encode('ascii')) #broadcast message with timestamp prefix
                log_message(sender, 'general', message.split(': ', 1)[1] if ': ' in message else message) #log message to database, extract content after sender prefix

        except:
            index = clients.index(client) #find index of client that disconnected
            nickname = nicknames[index] #find corresponding nickname using index
            clients.remove(client) #remove client socket from list
            client.close() #close the disconnected client connection
            broadcast(f'{nickname} left the chat!'.encode('ascii')) #broadcast that client has left
            nicknames.remove(nickname) #remove nickname from list
            broadcast_userlist() #update online user list for all clients
            break