import sys
sys.path.append('..') #for parent directory imports

import socket
import threading
import customtkinter as ctk
from config import HOST, PORT, MAX_BUFFER, APP_NAME

#chatbuzz color pallete
BG_DARK      = '#080d08'
BG_MID       = '#0a0f0a'
BG_PANEL     = '#0d150d'
GREEN_BRIGHT = '#33cc33'
GREEN_DIM    = "#4cb94c"
GREEN_DARK   = '#2a7a2a'
GREEN_DARKER = '#1a3a1a'
BORDER       = "#112711"
FONT_MONO    = ('Courier', 14)
FONT_MONO_SM = ('Courier', 13)
FONT_MONO_LG = ('Courier', 15)

#main theme for application
ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('green')

class ChatBuzzApp:
    def __init__(self):
        self.nickname = None
        self.password = None
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stop_thread = False

        self.login_destroyed = False #flag to check if login window is destroyed, to prevent multiple error messages on failed connection attempts
        self.online_users = [] #to keep track of online users for displaying in sidebar
        self.pending_online_list = None #stores online list received before chat window is ready

        #login window
        self.login_window = ctk.CTk()
        self.login_window.title(APP_NAME)
        self.login_window.geometry('500x320')
        self.login_window.configure(fg_color=BG_DARK)
        self.login_window.resizable(False, False)

        #ascii header
        ctk.CTkLabel(
            self.login_window,
            text=f'> {APP_NAME} // SECURE TERMINAL',
            font=FONT_MONO_LG,
            text_color=GREEN_BRIGHT
        ).pack(pady=(28, 4))

        ctk.CTkLabel(
            self.login_window,
            text='--------------------------------',
            font=FONT_MONO_SM,
            text_color=GREEN_DIM
        ).pack()

        #nickname input label
        ctk.CTkLabel(
            self.login_window,
            text='ENTER USERNAME:',
            font=FONT_MONO_SM,
            text_color=GREEN_BRIGHT
        ).pack(pady=(16, 4))

        #nickname input field
        self.nickname_input = ctk.CTkEntry(
            self.login_window,
            placeholder_text='text here...',
            font=FONT_MONO,
            fg_color=BG_PANEL,
            border_color=BORDER,
            text_color=GREEN_BRIGHT,
            width=260
        )
        self.nickname_input.pack(pady=4)
        self.nickname_input.bind('<Return>', lambda e: self.login())

        #error label — empty by default, shows red text on errors
        self.login_error = ctk.CTkLabel(
            self.login_window,
            text='',
            font=FONT_MONO_SM,
            text_color='#cc3333'
        )
        self.login_error.pack()

        #connect button
        ctk.CTkButton(
            self.login_window,
            text='[ CONNECT ]',
            font=FONT_MONO,
            fg_color=BG_PANEL,
            hover_color='#1a4a1a',
            border_width=1,
            border_color=GREEN_DARK,
            text_color=GREEN_BRIGHT,
            width=260,
            command=self.login
        ).pack(pady=8)

    #function to start application
    def run(self):
        self.login_window.mainloop() #starts the login window, keeps running until closed

    #function to handle login logic, called when user clicks connect button or presses Enter in nickname field
    def login(self):
        self.password = None #reset password on each login attempt
        self.nickname = self.nickname_input.get() #gets nickname from the input field
        if not self.nickname: #if nickname is empty, show error message
            self.login_error.configure(text='[ERROR] username cannot be empty')
            return
        if self.nickname == 'admin': #if nickname is admin, ask for password
            self.password = self.ask_password() #calls function to ask for admin password, stores it in self.password
            if not self.password: #cancelled or empty
                return

        self.setup_socket() #calls function to setup socket connection

    def update_online_list(self, users):
    #clear existing online labels and rebuild with updated user list
        for widget in self.online_frame.winfo_children(): #destroy existing labels
            widget.destroy()
        for user in users: #add new label for each user
            if user: #ignore empty strings
                color = GREEN_BRIGHT if user == self.nickname else GREEN_DARK #highlight self
                ctk.CTkLabel(self.online_frame, text=f'● {user}', font=FONT_MONO_SM, text_color=color).pack(pady=2, anchor='w')
        self.online_header.configure(text=f'// ONLINE ({len([u for u in users if u])})') #update count

    #function to disable chat input when user is kicked or banned
    def disable_chat(self, reason):
        self.message_input.configure(
            state='disabled', #disable input field
            placeholder_text=f'[ {reason} ]', #show reason in placeholder
            fg_color='#050a05' #darker background to signal disabled state
        )
        self.send_button.configure(
            state='disabled', #disable send button
            fg_color='#050a05', #darker background
            text_color='#1a3a1a' #dim text to signal disabled state
        )

    #function to receive messages from server, runs in a separate thread
    def receive(self):
        while True:
            try:
                raw = self.client.recv(MAX_BUFFER).decode('ascii') #receives raw data from server
                messages = raw.split('\n') #split in case multiple messages arrived together due to tcp buffering

                for message in messages:
                    message = message.strip() #remove whitespace and newlines
                    if not message: continue #skip empty strings from split

                    if message == 'NICKNAME':
                        self.client.send(self.nickname.encode('ascii')) #sends nickname to server when asked
                        if self.password:
                            next_msg = self.client.recv(MAX_BUFFER).decode('ascii') #receives next message from server
                            if next_msg == 'PASSWORD':
                                self.client.send(self.password.encode('ascii')) #sends password to server when asked
                                auth_response = self.client.recv(MAX_BUFFER).decode('ascii') #receives authentication response
                                if auth_response == 'INCORRECT_PASSWORD': #if incorrect password, show error and stop
                                    self.login_window.after(0, lambda: self.login_error.configure(
                                        text='[REFUSED] incorrect admin password'
                                    ))
                                    return

                    elif message == 'BAN': #server sent ban message, show error on login window and stop
                        self.client.close()
                        self.login_window.after(0, lambda: self.login_error.configure(
                            text='[REFUSED] you are banned from this server'
                        ))
                        return

                    elif message.startswith('USERLIST:'): #server sent updated online list
                        users = message[9:].split(',') #extract usernames from message
                        if self.login_destroyed: #chat window is ready, update immediately
                            self.chat_window.after(0, lambda u=users: self.update_online_list(u))
                        else:
                            self.pending_online_list = users #store for later if chat window not ready yet

                    else:
                        if not self.login_destroyed: #only runs once on first successful message
                            self.login_destroyed = True
                            self.login_window.after(0, self.login_window.destroy) #close login window
                            self.chat_window.after(0, self.chat_window.deiconify) #show chat window
                            if self.pending_online_list: #apply stored online list if it arrived before window was ready
                                self.chat_window.after(100, lambda u=self.pending_online_list: self.update_online_list(u))

                        if 'has been kicked' in message or 'has been banned' in message:
                            username = message.split(' ')[0] #first word is always the username
                            if username == self.nickname: #if it's this client who was kicked/banned
                                reason = 'you were kicked' if 'kicked' in message else 'you were banned'
                                self.chat_window.after(0, lambda r=reason: self.disable_chat(r))

                        self.chat_window.after(0, lambda msg=message: self.display_message(msg)) #display message in chat window

            except:
                break #if connection is lost, exit receive loop, thread will end

    #function to ask admin password using a dialog, returns the entered password
    def ask_password(self):
        result = [None] #empty list to store result from nested function, can be modified from inner scope

        #dialog window for admin password input
        dialog = ctk.CTkToplevel(self.login_window)
        dialog.title(f'{APP_NAME} // ADMIN AUTH')
        dialog.geometry('460x260')
        dialog.configure(fg_color=BG_DARK)
        dialog.resizable(False, False)
        dialog.grab_set()

        #admin auth dialog UI
        ctk.CTkLabel(dialog, text='> ADMIN AUTH // SECURE TERMINAL', font=FONT_MONO_LG, text_color=GREEN_BRIGHT).pack(pady=(24,4))
        ctk.CTkLabel(dialog, text='--------------------------------', font=FONT_MONO_SM, text_color=GREEN_DIM).pack()
        ctk.CTkLabel(dialog, text='ENTER ADMIN KEY:', font=FONT_MONO_SM, text_color=GREEN_BRIGHT).pack(pady=(16,4))

        #password input field, show='*' to hide input
        pwd_input = ctk.CTkEntry(dialog, font=FONT_MONO, fg_color=BG_PANEL, border_color=BORDER, text_color=GREEN_BRIGHT, width=260, show='*')
        pwd_input.pack(pady=4)

        def confirm(): #nested function to get password and close dialog
            result[0] = pwd_input.get() #get password from input field, store in result list
            dialog.destroy() #close dialog after getting password

        #allow pressing Enter to confirm password
        pwd_input.bind('<Return>', lambda e: confirm())
        ctk.CTkButton(dialog, text='[ AUTHENTICATE ]', font=FONT_MONO, fg_color=BG_PANEL, hover_color='#1a4a1a', border_width=1, border_color=GREEN_DARK, text_color=GREEN_BRIGHT, width=260, command=confirm).pack(pady=8)

        #wait for dialog to close before returning result
        dialog.wait_window()
        return result[0]

    #function to send message to server
    def send_message(self):
        message = self.message_input.get()

        if not message: return #if message is empty, do nothing

        if message.startswith('/kick '): #translate kick command to server protocol
            self.client.send(f'KICK {message[6:]}'.encode('ascii'))
        elif message.startswith('/ban '): #translate ban command to server protocol
            self.client.send(f'BAN {message[5:]}'.encode('ascii'))
        elif message.startswith('/unban '): #translate unban command to server protocol
            self.client.send(f'UNBAN {message[7:]}'.encode('ascii'))
        else:
            self.client.send(f'{self.nickname}: {message}'.encode('ascii')) #send normal message with nickname prefix

        self.message_input.delete(0, 'end') #clear input field after sending message

    #function to display message in chat box, runs in main thread using after() to avoid tkinter threading issues
    def display_message(self, message):
        self.chat_box.configure(state='normal') #enable editing of chat box to insert new message
        self.chat_box.insert('end', message + '\n') #insert message at the end of the chat box, add newline for separation
        self.chat_box.configure(state='disabled') #disable editing of chat box to prevent user from changing messages
        self.chat_box.see('end') #scroll to the end of chat box to show latest message

    #function to handle closing of chat window, makes sure socket connection is closed and thread is stopped
    def on_close(self):
        self.stop_thread = True
        self.client.close()
        self.chat_window.destroy()
        sys.exit() #force exit to ensure all threads are closed, daemon threads may not close properly on their own (fix)


    #function to setup socket connection, connect to server, start chat window
    def setup_socket(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #fresh socket instance for each connection attempt
            self.client.connect((HOST, PORT)) #connects to server using config host and port

            #chat window
            self.chat_window = ctk.CTk()
            self.chat_window.title(f'{APP_NAME} // {self.nickname}')
            self.chat_window.geometry('900x600')
            self.chat_window.configure(fg_color=BG_DARK)
            self.chat_window.withdraw() #hide until login confirmed

            #top bar — packed first so it stays at top
            top_bar = ctk.CTkFrame(self.chat_window, fg_color=BG_PANEL, corner_radius=0, height=36)
            top_bar.pack(fill='x', side='top')
            top_bar.pack_propagate(False)
            ctk.CTkLabel(top_bar, text=f'{APP_NAME} // v1.0.0 // SECURE TERMINAL', font=FONT_MONO_SM, text_color=GREEN_DIM).pack(side='left', padx=14, pady=8)
            ctk.CTkLabel(top_bar, text=f'NODE: {self.nickname}', font=FONT_MONO_SM, text_color=GREEN_DIM).pack(side='right', padx=14)

            #bottom bar — packed second so it stays at bottom
            bottom_bar = ctk.CTkFrame(self.chat_window, fg_color=BG_PANEL, corner_radius=0, height=44)
            bottom_bar.pack(fill='x', side='bottom')
            bottom_bar.pack_propagate(False)
            ctk.CTkLabel(bottom_bar, text=f'{self.nickname}@chatbuzz:~$', font=FONT_MONO_SM, text_color=GREEN_BRIGHT).pack(side='left', padx=(12,4), pady=10)
            
            self.send_button = ctk.CTkButton(bottom_bar, text='SEND', font=FONT_MONO_SM, fg_color=BG_PANEL, hover_color='#1a4a1a', border_width=1, border_color=GREEN_DARK, text_color=GREEN_BRIGHT, width=70, command=self.send_message)
            self.send_button.pack(side='right', padx=10, pady=8)
            ctk.CTkLabel(bottom_bar, text='/kick /ban /unban', font=FONT_MONO_SM, text_color=GREEN_DARKER).pack(side='right', padx=4)

            #message input
            self.message_input = ctk.CTkEntry(bottom_bar, font=FONT_MONO_SM, fg_color=BG_PANEL, border_width=0, text_color=GREEN_BRIGHT, placeholder_text='type a message or /command...', placeholder_text_color=GREEN_DIM)
            self.message_input.pack(side='left', fill='x', expand=True, pady=8)
            self.message_input.bind('<Return>', lambda e: self.send_message()) #enter key to send

            #main content — fills remaining space between top and bottom bars
            main_frame = ctk.CTkFrame(self.chat_window, fg_color=BG_DARK)
            main_frame.pack(fill='both', expand=True)

            #sidebar
            self.sidebar = ctk.CTkFrame(main_frame, fg_color=BG_PANEL, width=180, corner_radius=0)
            self.sidebar.pack(side='left', fill='y')
            self.sidebar.pack_propagate(False) #prevents sidebar from shrinking

            #sidebar online users section
            self.online_header = ctk.CTkLabel(self.sidebar, text='// ONLINE (0)', font=FONT_MONO_SM, text_color=GREEN_DIM) #header for online users list, updated dynamically with number of users
            self.online_header.pack(pady=(12,4), padx=10, anchor='w')

            #online users list frame — individual labels added dynamically
            self.online_frame = ctk.CTkFrame(self.sidebar, fg_color='transparent') #transparent frame to hold online user labels
            self.online_frame.pack(fill='x', padx=10, anchor='w')

            #right chat area
            right_frame = ctk.CTkFrame(main_frame, fg_color=BG_DARK, corner_radius=0)
            right_frame.pack(side='left', fill='both', expand=True)

            #chat display
            self.chat_box = ctk.CTkTextbox(right_frame, font=FONT_MONO, fg_color=BG_MID, text_color=GREEN_BRIGHT, border_color=BORDER, border_width=1, wrap='word')
            self.chat_box.pack(padx=10, pady=10, fill='both', expand=True)
            self.chat_box.configure(state='disabled')

            self.display_message('[SYS] --- session established ---') #boot message on connect

            thread = threading.Thread(target=self.receive) #create thread for receiving messages
            thread.daemon = True #thread closes automatically when main program exits
            thread.start()

            self.chat_window.protocol('WM_DELETE_WINDOW', self.on_close) #handle window close event
            self.chat_window.mainloop() #start chat window, keeps running until closed

        except Exception as e:
            self.login_error.configure(text='[ERR] connection failed — is server running?') #error message if connection fails

if __name__ == '__main__': #starts application if run directly
    app = ChatBuzzApp()
    app.run()