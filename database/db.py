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
    conn.commit()
    conn.close()