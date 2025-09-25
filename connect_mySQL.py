import mysql.connector


connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="17101975",
    database="bookstore"
)

cursor = connection.cursor()


cursor.execute("SELECT * FROM books;")

rows = cursor.fetchall()

print("Danh sách sách trong Bookstore:")
for row in rows:
    print(row)

cursor.close()
connection.close()
