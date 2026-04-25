import sys
sys.path.append('..') #for parent directory imports

import socket
import threading
import customtkinter as ctk
from config import HOST, PORT, MAX_BUFFER, APP_NAME

#main theme for application
ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('green')

class ChatBuzzApp:
    def __init__(self):
        self.nickname = None
        self.password = None
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stop_thread = False

        #creating login window using customtkinter
        self.login_window = ctk.CTk()
        self.login_window.title(f'{APP_NAME} - Login')
        self.login_window.geometry('400x300')

        #label and entry for nickname
        self.nickname_label = ctk.CTkLabel(self.login_window, text='Enter your nickname')
        self.nickname_input = ctk.CTkEntry(self.login_window, placeholder_text='nickname...') #placeholder text for input field
        self.entry_button = ctk.CTkButton(self.login_window, text='Connect', command=self.login) #calls login function when button is clicked

        #putting padding around widgets, packing them into 400x300 window
        self.nickname_label.pack(pady=10)
        self.nickname_input.pack(pady=10)
        self.entry_button.pack(pady=10)

    def run(self):
        self.login_window.mainloop() #starts the login window, keeps running until closed

    def login(self):
        self.nickname = self.nickname_input.get() #gets nickname from the input field
        if not self.nickname: #if nickname is empty, show error message
            ctk.CTkLabel(self.login_window, text='Nickname cannot be empty!', text_color='red').pack()
            return
        if self.nickname == 'admin': #if nickname is admin, ask for password
            self.password = ctk.CTkInputDialog(text='Enter admin password:', title='Admin Login').get_input()
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
                            self.client.send(self.password.encode('ascii')) #sends password to server if asked
                else:
                    self.display_message(message) #displays message in chat window, replaces print
            except:
                break


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


    def display_message(self, message):
        self.chat_box.configure(state='normal') #enable editing of chat box to insert new message
        self.chat_box.insert('end', message + '\n') #insert message at the end of the chat box, add newline for separation
        self.chat_box.configure(state='disabled') #disable editing of chat box to prevent user from changing messages
        self.chat_box.see('end') #scroll to the end of chat box to show latest message

    #function to setup socket connection, connect to server, start chat window
    def setup_socket(self):
        try:
            self.client.connect((HOST, PORT)) #connects to server using config host and port
            self.login_window.destroy() #close login window after successful connection

            #create chat window
            self.chat_window = ctk.CTk()
            self.chat_window.title(f'{APP_NAME} - {self.nickname}')
            self.chat_window.geometry('500x500')

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

            self.chat_window.mainloop() #start chat window, keep running until closed

        except Exception as e:
            ctk.CTkLabel(self.login_window, text='Connection failed!', text_color='red').pack() #error message if connection fails

if __name__ == '__main__': #starts application if run directly
    app = ChatBuzzApp()
    app.run()