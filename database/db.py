import sqlite3

def init_db():
    conn = sqlite3.connect('chatbuzz.db')
    cursor = conn.cursor()
 
    cursor.execute('CREATE TABLE IF NOT EXISTS bans (nickname TEXT)') #creates a table for banned users if it doesn't exist

    #creates a table for messages if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            sender TEXT,    --who sent the message
            channel TEXT,   --which channel the message was sent in
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,   --when the message was sent
            message TEXT    --the message content
        )
    ''')
    conn.commit() #for changing database we commit changes
    conn.close()

def add_ban(nickname):
    conn = sqlite3.connect('chatbuzz.db')
    cursor = conn.cursor()

    #add a new row into bans table with nickname column set to the provided nickname
    cursor.execute('INSERT INTO bans (nickname) VALUES (?)', (nickname,)) #replace ? with provided nickname, using comma for tuple
    conn.commit()
    conn.close()

def is_banned(nickname):
    conn = sqlite3.connect('chatbuzz.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM bans WHERE nickname = ?', (nickname,)) #selects all rows from bans table where nickname column matches provided nickname
    result = cursor.fetchone() #fetches the first row of result if match found, else returns None
    conn.close()
    return result is not None #return true is match found, else false


def remove_ban(nickname):
    conn = sqlite3.connect('chatbuzz.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM bans WHERE nickname = ?', (nickname,)) #deletes rows from bans table where nickname column matches provided nickname
    conn.commit()
    conn.close()

#function to log messages into the database
def log_message(sender, channel, message):
    conn = sqlite3.connect('chatbuzz.db')
    cursor = conn.cursor()

    #add a new row into messages table with the provided values
    cursor.execute('INSERT INTO messages (sender, channel, message) VALUES (?, ?, ?)', (sender, channel, message))
    conn.commit()
    conn.close()