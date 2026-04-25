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
        result = [None]  #empty list to store result from nested function, can be modified from inner scope
        
        #dialog window for admin password input
        dialog = ctk.CTkToplevel(self.login_window)
        dialog.title(f'{APP_NAME} // ADMIN AUTH')
        dialog.geometry('420x240')
        dialog.configure(fg_color=BG_DARK)
        dialog.resizable(False, False)
        dialog.grab_set()

        #admin auth dialog UI
        ctk.CTkLabel(dialog, text='> ADMIN AUTH // SECURE TERMINAL', font=FONT_MONO_LG, text_color=GREEN_BRIGHT).pack(pady=(24,4))
        ctk.CTkLabel(dialog, text='──────────────────────────────', font=FONT_MONO_SM, text_color=GREEN_DIM).pack()
        ctk.CTkLabel(dialog, text='ENTER ADMIN KEY:', font=FONT_MONO_SM, text_color=GREEN_MID).pack(pady=(16,4))

        #password input field, show='*' to hide input
        pwd_input = ctk.CTkEntry(dialog, font=FONT_MONO, fg_color=BG_PANEL, border_color=BORDER, text_color=GREEN_BRIGHT, width=260, show='*')
        pwd_input.pack(pady=4)

        def confirm(): #nested function to get password and close dialog
            result[0] = pwd_input.get() #get password from input field, store in result list
            dialog.destroy() #close dialog after getting password

        #allow pressing Enter to confirm password
        pwd_input.bind('<Return>', lambda e: confirm())
        ctk.CTkButton(dialog, text='[ AUTHENTICATE ]', font=FONT_MONO, fg_color=BG_PANEL, hover_color='#1a4a1a', border_width=1, border_color=GREEN_MID, text_color=GREEN_BRIGHT, width=260, command=confirm).pack(pady=8)

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
            self.chat_window.title(f'{APP_NAME} // {self.nickname.upper()}')
            self.chat_window.geometry('780x540')
            self.chat_window.configure(fg_color=BG_DARK)
            self.chat_window.withdraw() #hide until login confirmed

            #top bar
            top_bar = ctk.CTkFrame(self.chat_window, fg_color=BG_PANEL, corner_radius=0, height=36)
            top_bar.pack(fill='x')
            top_bar.pack_propagate(False)

            ctk.CTkLabel(
                top_bar,
                text=f'{APP_NAME} // v1.0.0 // SECURE TERMINAL',
                font=FONT_MONO_SM,
                text_color=GREEN_DIM
            ).pack(side='left', padx=14, pady=8)

            ctk.CTkLabel(
                top_bar,
                text=f'NODE: {self.nickname.upper()}',
                font=FONT_MONO_SM,
                text_color=GREEN_MID
            ).pack(side='right', padx=14)

            #chat display
            self.chat_box = ctk.CTkTextbox(
                self.chat_window,
                font=FONT_MONO_SM,
                fg_color=BG_MID,
                text_color=GREEN_BRIGHT,
                border_color=BORDER,
                border_width=1,
                wrap='word'
            )
            self.chat_box.pack(padx=10, pady=10, fill='both', expand=True)
            self.chat_box.configure(state='disabled')

            #bottom bar
            bottom_bar = ctk.CTkFrame(self.chat_window, fg_color=BG_PANEL, corner_radius=0, height=44)
            bottom_bar.pack(fill='x', side='bottom')
            bottom_bar.pack_propagate(False)

            #prompt label
            ctk.CTkLabel(
                bottom_bar,
                text=f'{self.nickname}@chatbuzz:~$',
                font=FONT_MONO_SM,
                text_color=GREEN_BRIGHT
            ).pack(side='left', padx=(12,4), pady=10)

            #message input
            self.message_input = ctk.CTkEntry(
                bottom_bar,
                font=FONT_MONO_SM,
                fg_color=BG_PANEL,
                border_width=0,
                text_color=GREEN_BRIGHT,
                placeholder_text='type a message or /command...',
                placeholder_text_color=GREEN_DIM
            )
            self.message_input.pack(side='left', fill='x', expand=True, pady=8)
            self.message_input.bind('<Return>', lambda e: self.send_message()) #enter key to send

            #command hint
            ctk.CTkLabel(
                bottom_bar,
                text='/kick /ban /unban /who /dm',
                font=('Courier', 9),
                text_color=GREEN_DIM
            ).pack(side='right', padx=4)

            #send button
            ctk.CTkButton(
                bottom_bar,
                text='SEND',
                font=FONT_MONO_SM,
                fg_color=BG_PANEL,
                hover_color='#1a4a1a',
                border_width=1,
                border_color=GREEN_MID,
                text_color=GREEN_BRIGHT,
                width=70,
                command=self.send_message
            ).pack(side='right', padx=10, pady=8)

            thread = threading.Thread(target=self.receive) #create thread for receiving messages
            thread.daemon = True #thread closes automatically when main program exits
            thread.start()

            self.chat_window.protocol('WM_DELETE_WINDOW', self.on_close) #handle window close
            self.chat_window.mainloop() #start chat window, keeps running until closed

        except Exception as e:
            self.login_error.configure(text='[ERR] connection failed — is server running?') #error message if connection fails

if __name__ == '__main__': #starts application if run directly
    app = ChatBuzzApp()
    app.run()