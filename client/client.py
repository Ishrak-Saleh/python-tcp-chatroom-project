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
            ctk.CTkLabel(self.login_window, text='Nickname cannot be empty!', text_color='red').pack() #error message label, packed below the button
            return
        if self.nickname == 'admin': #if nickname is admin, ask for password
            self.password = ctk.CTkInputDialog(text='Enter admin password:', title='Admin Login').get_input() #shows input dialog for password, gets input from user
            if not self.password:  # cancelled or empty
                return

        self.setup_socket() #calls function to setup socket connection

    #function to receive messages from server, runs in a separate thread
    def receive(self):
        pass
    
    #function to setup socket connection, connect to server, send nickname and password if admin, start thread for receiving messages
    def setup_socket(self):
        try:
            self.client.connect((HOST, PORT)) #connects to server using config host and port

            #close login window, open chat window
            self.login_window.destroy()
            self.chat_window = ctk.CTk() #creates new window for chat
            self.chat_window.title(f'{APP_NAME} - {self.nickname}')
            self.chat_window.geometry('500x500')

            thread = threading.Thread(target=self.receive) #create thread for receiving messages from server, run receive function in that thread
            thread.daemon = True #thread closes automatically when main program exits
            thread.start()

            self.chat_window.mainloop() #start chat window, keep running until closed
        
        except Exception as e:
            ctk.CTkLabel(self.login_window, text=f'Connection failed!', text_color='red').pack() #error message if connection fails

        

if __name__ == '__main__': #starts application if run directly
    app = ChatBuzzApp()
    app.run()