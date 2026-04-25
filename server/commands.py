from server.state import clients, nicknames, broadcast
from database.db import add_ban, remove_ban

#function to kick user from server
def kick_user(username):
    if username in nicknames:
        name_index = nicknames.index(username) #finds index of username in nicknames list
        client_to_kick = clients[name_index] #finds corresponding client using index
        
        clients.remove(client_to_kick) #removes client from the clients list
        client_to_kick.send(f'You have been kicked from the server!'.encode('ascii')) #sends message to kicked client
        client_to_kick.close() #closes the client connection
        
        nicknames.remove(username) #removes username from nicknames list
        
        broadcast(f'{username} has been kicked from the chat!'.encode('ascii')) #broadcasts message to all clients


#function to ban user from server
def ban_user(username):
    if username == 'admin': 
        broadcast('You cannot ban an admin!'.encode('ascii'))
        return

    if username in nicknames:
        name_index = nicknames.index(username) #finds index of username in nicknames list
        client_to_ban = clients[name_index] #finds corresponding client using idnex
        
        clients.remove(client_to_ban) #removes client from the clients list
        client_to_ban.send(f'You have been banned from the server!'.encode('ascii')) #sends message to banned client
        client_to_ban.close() #closes the client connection
        
        add_ban(username) #adds the username to the bans list in the database
        
        nicknames.remove(username) #removes username from nicknames list
        broadcast(f'{username} has been banned from the chat!'.encode('ascii')) #broadcasts message to all clients

#function to unban user from server
def unban_user(username):
    remove_ban(username) #calls db function to remove the ban from user in database
    broadcast(f'{username} has been unbanned from the chat!'.encode('ascii')) #broadcasts message to all clients