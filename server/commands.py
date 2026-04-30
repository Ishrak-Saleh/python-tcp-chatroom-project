from server.state import clients, nicknames, broadcast, broadcast_userlist, groups, broadcast_group, make_group_id
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


#function to create a new group and invite targets
def group_invite(inviter, targets):
    #filter targets to only online users, exclude inviter
    valid = [t for t in targets if t in nicknames and t != inviter]
    if not valid:
        idx = nicknames.index(inviter)
        clients[idx].send('[SYS] No valid users to invite.\n'.encode('ascii'))
        return

    group_id = make_group_id(inviter, valid)
    inviter_sock = clients[nicknames.index(inviter)]

    #create group with only inviter for now
    groups[group_id] = {
        'members': [inviter],
        'sockets': [inviter_sock]
    }

    #notify inviter that group was created
    inviter_sock.send(f'GROUP_CREATED {group_id}\n'.encode('ascii'))

    #send invite request to each valid target
    for target in valid:
        target_sock = clients[nicknames.index(target)]
        target_sock.send(f'GROUP_INVITE_REQ {group_id} {inviter}\n'.encode('ascii'))


#function to add accepting member to group
def group_accept(group_id, nickname):
    if group_id not in groups: return
    if nickname in groups[group_id]['members']: return

    sock = clients[nicknames.index(nickname)]
    groups[group_id]['members'].append(nickname)
    groups[group_id]['sockets'].append(sock)

    #notify new member
    members_str = ','.join(groups[group_id]['members'])
    sock.send(f'GROUP_JOINED {group_id} {members_str}\n'.encode('ascii'))

    #broadcast join to existing members
    broadcast_group(group_id, f'GROUP_MSG {group_id} [SYS] {nickname} joined the group!'.encode('ascii'))


#function to remove a member from group, dissolve if empty
def group_leave(group_id, nickname):
    if group_id not in groups: return
    if nickname not in groups[group_id]['members']: return

    idx = groups[group_id]['members'].index(nickname)
    groups[group_id]['members'].pop(idx)
    groups[group_id]['sockets'].pop(idx)

    #notify remaining members
    broadcast_group(group_id, f'GROUP_MSG {group_id} [SYS] {nickname} left the group!'.encode('ascii'))

    #dissolve if empty
    if not groups[group_id]['members']:
        del groups[group_id]
    

#function to relay a message inside a group
def group_send(group_id, sender, message):
    if group_id not in groups: return
    broadcast_group(group_id, f'GROUP_MSG {group_id} {sender}: {message}'.encode('ascii'))