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
GREEN_DIM    = '#1f5a1f'
GREEN_MID    = '#2a7a2a'
BORDER       = '#1a3a1a'
FONT_MONO    = ('Courier', 12)
FONT_MONO_SM = ('Courier', 11)
FONT_MONO_LG = ('Courier', 14)

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

        #creating login window using customtkinter
        #login window
        self.login_window = ctk.CTk()
        self.login_window.title(APP_NAME)
        self.login_window.geometry('500x300')
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
            text='──────────────────────────────',
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
            border_color=GREEN_MID,
            text_color=GREEN_BRIGHT,
            width=260,
            command=self.login
        ).pack(pady=8)
    
    #function to start application
    def run(self):
        self.login_window.mainloop() #starts the login window, keeps running until closed

    #function to handle login logic, called when user clicks connect button or presses Enter in nickname field
    def login(self):
        self.nickname = self.nickname_input.get() #gets nickname from the input field
        if not self.nickname: #if nickname is empty, show error message
            self.login_error.configure(text='[ERROR] username cannot be empty')
            return
        if self.nickname == 'admin': #if nickname is admin, ask for password
            self.password = self.ask_password() #calls function to ask for admin password, stores it in self.password
            if not self.password: #cancelled or empty
                return

        self.setup_socket() #calls function to setup socket connection

    #function to receive messages from server, runs in a separate thread
    def receive(self):
        while True:
            try:
                message = self.client.recv(MAX_BUFFER).decode('ascii') #receives message from server, decodes it, if error occurs it means connection is lost
                if message == 'NICKNAME':
                    self.client.send(self.nickname.encode('ascii')) #sends nickname to server when asked
                    if self.password:
                        next_msg = self.client.recv(MAX_BUFFER).decode('ascii') #receives next message from server, checks if it's asking for password
                        if next_msg == 'PASSWORD':
                            self.client.send(self.password.encode('ascii')) #sends password to server when asked
                            auth_response = self.client.recv(MAX_BUFFER).decode('ascii') #receives authentication response from server
                            if auth_response == 'INCORRECT_PASSWORD': #if incorrect password, close connection and show error message
                                self.login_window.after(0, lambda: self.login_error.configure(
                                    text='[REFUSED] incorrect admin password'
                                ))
                                return
                            
                elif message == 'BAN':
                    self.client.close()
                    self.login_window.after(0, lambda: self.login_error.configure(
                        text='[REFUSED] you are banned from this server'
                    ))
                    return

                else:
                    if not self.login_destroyed: #only destroy login window once
                        self.login_destroyed = True
                        self.login_window.after(0, self.login_window.destroy) #close login window after successful connection
                        self.chat_window.after(0, self.chat_window.deiconify) #show chat window after successful connection
                    self.display_message(message) #displays message in chat window, replaces print
            except:
                break

    #function to ask admin password using a dialog, returns the entered password
    def ask_password(self):
        dialog = ctk.CTkInputDialog(
            text='ENTER ADMIN KEY:',
            title=f'{APP_NAME} // ADMIN AUTH',
        )
        dialog.configure(fg_color=BG_DARK) #dialog background color
        return dialog.get_input() #returns input entered by user in dialog

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

            #create chat window
            self.chat_window = ctk.CTk()
            self.chat_window.title(f'{APP_NAME} - {self.nickname}')
            self.chat_window.geometry('500x500')

            self.chat_window.withdraw()  #hide chat window till login is successful

            #chat display
            self.chat_box = ctk.CTkTextbox(self.chat_window, state='disabled')
            self.chat_box.pack(padx=10, pady=10, fill='both', expand=True)

            #bottom bar
            self.input_frame = ctk.CTkFrame(self.chat_window)
            self.input_frame.pack(padx=10, pady=5, fill='x')

            #message input field
            self.message_input = ctk.CTkEntry(self.input_frame, placeholder_text='Type a message...')
            self.message_input.pack(side='left', fill='x', expand=True, padx=5)

            self.message_input.bind('<Return>', lambda e: self.send_message()) #user can press Enter to send message

            #send button
            self.send_button = ctk.CTkButton(self.input_frame, text='Send', width=80, command=self.send_message)
            self.send_button.pack(side='right', padx=5)

            thread = threading.Thread(target=self.receive) #create thread for receiving messages
            thread.daemon = True #thread closes automatically when main program exits
            thread.start()

            self.chat_window.protocol('WM_DELETE_WINDOW', self.on_close) #handle window close event to clean up resources
            self.chat_window.mainloop() #start chat window, keep running until closed

        except Exception as e:
            self.login_error.configure(text='[ERR] connection failed — is server running?') #error message if connection fails

if __name__ == '__main__': #starts application if run directly
    app = ChatBuzzApp()
    app.run()