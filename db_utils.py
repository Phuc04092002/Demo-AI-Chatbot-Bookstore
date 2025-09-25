import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="17101975",
        database="bookstore"
    )

def fetch_books():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT book_id, title, author, price, stock, category FROM books;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

if __name__ == "__main__":
    for book in fetch_books():
        print(book)
