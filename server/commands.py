from server.state import clients, nicknames, broadcast, broadcast_userlist
from database.db import add_ban, remove_ban

#function to kick user from server
def kick_user(username):
    if username not in nicknames:
        return

    name_index = nicknames.index(username) #finds index of username in nicknames list
    client_to_kick = clients[name_index] #finds corresponding client using index

    client_to_kick.send('You have been kicked from the server!\n'.encode('ascii')) #sends message to kicked client
    # Give the message a moment to flush before closing
    import time; time.sleep(0.05)

    clients.remove(client_to_kick) #removes client from the clients list
    client_to_kick.close() #closes the client connection
    nicknames.remove(username) #removes username from nicknames list

    broadcast(f'{username} has been kicked from the chat!'.encode('ascii')) #broadcasts message to all clients
    broadcast_userlist() #update online list for all clients


#function to ban user from server
def ban_user(username):
    if username == 'admin':
        broadcast('You cannot ban an admin!'.encode('ascii'))
        return

    if username not in nicknames:
        return

    name_index = nicknames.index(username) #finds index of username in nicknames list
    client_to_ban = clients[name_index] #finds corresponding client using index

    client_to_ban.send('You have been banned from the server!\n'.encode('ascii')) #sends message to banned client
    import time; time.sleep(0.05) #giving message time before closing

    clients.remove(client_to_ban) #removes client from the clients list
    client_to_ban.close() #closes the client connection
    add_ban(username) #adds the username to the bans list in the database
    nicknames.remove(username) #removes username from nicknames list

    broadcast(f'{username} has been banned from the chat!'.encode('ascii')) #broadcasts message to all clients
    broadcast_userlist() #update online list for all clients


#function to unban user from server
def unban_user(username):
    remove_ban(username) #calls db function to remove the ban from user in database
    broadcast(f'{username} has been unbanned from the chat!'.encode('ascii')) #broadcasts message to all clients
    broadcast_userlist() #update online list for all clients