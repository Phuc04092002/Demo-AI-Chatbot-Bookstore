import mysql.connector
import joblib
from sentence_transformers import SentenceTransformer
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from fuzzywuzzy import process
import re
import json


embed_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
clf = joblib.load("../model/model_xgb_1.pkl")
label_encoder = joblib.load("../model/label_encoder_1.pkl")


def classify_intent(user_input: str) -> str:
    emb = embed_model.encode([user_input])
    pred_label = clf.predict(emb)[0]
    intent = label_encoder.inverse_transform([pred_label])[0]
    return intent



def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="17101975",
        database="bookstore"
    )


def extract_book_title(user_input: str) -> str:
    # regex lấy tên sách (trước từ khóa giá, cuốn, tập...)
    m = re.search(r'(?:(?:cuốn|quyển)\s+)?(.+?)(?:\s*(giá|còn|tìm|thông tin|còn bao nhiêu|,|$))',
                  user_input, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return user_input.strip()

def lookup_book(book_title: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT title, author, price, stock, category FROM books WHERE title LIKE %s"
    cursor.execute(query, (f"%{book_title}%",))
    results = cursor.fetchall()

    if not results:
        cursor.execute("SELECT title, author, price, stock, category FROM books")
        all_books = cursor.fetchall()
        titles = [r[0] for r in all_books]

        best_match, score = process.extractOne(book_title, titles)
        if score >= 85:  # ngưỡng độ chính xác
            for r in all_books:
                if r[0] == best_match:
                    results = [r]
                    break

    conn.close()

    if results:
        resp = []
        for r in results:
            resp.append(f"{r[0]} của {r[1]}, giá {r[2]}, còn {r[3]} quyển, thể loại {r[4]}")
        return "\n".join(resp)
    else:
        return f"Không tìm thấy sách '{book_title}'."


llm = Ollama(model="llama3.2:1b")
entity_prompt = PromptTemplate(
    input_variables=["user_input"],
    template="""
Bạn là extractor cho chatbot BookStore. Trả về JSON với các trường:
"book_title", "quantity", "address", "phone".
Chỉ trả về JSON, KHÔNG giải thích.
Câu: {user_input}
"""
)
chain = entity_prompt | llm

VIETNAMESE_NUMBERS = {
    "một": 1, "mốt": 1,
    "hai": 2,
    "ba": 3,
    "bốn": 4, "tư": 4,
    "năm": 5, "lăm": 5,
    "sáu": 6,
    "bảy": 7,
    "tám": 8,
    "chín": 9,
    "mười": 10
}
def normalize_quantity(text: str) -> int:
    m = re.search(r'(\d+)\s*(?:cuốn|quyển|bản)', text, re.IGNORECASE)
    if m:
        return int(m.group(1))


    for word, num in VIETNAMESE_NUMBERS.items():
        if re.search(rf'{word}\s*(?:cuốn|quyển|bản)', text, re.IGNORECASE):
            return num

    return 1


def extract_order_entities(user_input: str) -> dict:
    try:

        json_str = chain.invoke({"user_input": user_input})
        if isinstance(json_str, dict) and "text" in json_str:
            json_str = json_str["text"]
        order = json.loads(json_str)

        order["book_title"] = order.get("book_title", "").strip().rstrip(",. ")
        order["quantity"] = int(order.get("quantity", 1))
        order["address"] = order.get("address", "Unknown").strip().rstrip(",. ")
        order["phone"] = order.get("phone", "Unknown").strip().rstrip(",. ")
        if not order["book_title"]:
            raise ValueError("Empty book_title from LLM")
        return order

    except Exception as e:
        print("LLM parse fail:", e, "| Input:", user_input)

        phone_match = re.search(
            r'(?:số điện thoại|đt|phone)?[:\s]*([\d\s-]{5,15})',
            user_input,
            re.IGNORECASE
        )
        phone = re.sub(r'[\s-]', '', phone_match.group(1)) if phone_match else "Unknown"

        temp_input = re.sub(
            r'(?:số điện thoại|đt|phone)?[:\s]*([\d\s-]{8,15})',
            '',
            user_input,
            flags=re.IGNORECASE
        )

        addr_match = re.search(
            r'(?:tới|đến|địa chỉ|giao|về|ở)\s+(.+?)(?=\s*(?:số điện thoại|đt|phone|,|$))',
            temp_input,
            re.IGNORECASE
        )
        address = addr_match.group(1).strip() if addr_match else "Unknown"
        if address != "Unknown":
            address = re.sub(r'[\s,\.]+$', '', address)

        # qty_match = re.search(r'(\d+)\s*(?:cuốn|quyển|bản)?', temp_input, re.IGNORECASE)
        # quantity = int(qty_match.group(1)) if qty_match else 1

        quantity = normalize_quantity(temp_input)

        book_match = re.search(
            r'(?:mua|đặt|tôi muốn đặt|tôi muốn mua)?\s*(?:một|hai|ba|\d+)?\s*(?:cuốn|quyển|bản)?\s*([^\d,\.]+?)(?=\s*(?:tới|đến|địa chỉ|ở|sdt|phone|,|$))',
            temp_input,
            re.IGNORECASE
        )
        book_title = book_match.group(1).strip() if book_match else "Unknown"

        return {
            "book_title": book_title,
            "quantity": quantity,
            "address": address,
            "phone": phone
        }


def place_order(order: dict, customer_name="Khách hàng") -> str:
    conn = get_db_connection()
    cursor = conn.cursor()

    book_title = order['book_title'].strip().rstrip(",. ").lower()

    cursor.execute(
        "SELECT book_id, title, stock FROM books WHERE LOWER(title) LIKE %s",
        (f"%{book_title}%",)
    )
    res = cursor.fetchone()

    if not res:
        cursor.execute("SELECT book_id, title, stock FROM books")
        all_books = cursor.fetchall()  # [(book_id, title, stock), ...]

        titles = [r[1] for r in all_books]
        best_match, score = process.extractOne(book_title, titles)

        if score >= 85:  # ngưỡng confidence
            for r in all_books:
                if r[1] == best_match:
                    res = r
                    break

    if not res:
        conn.close()
        return f"Không tìm thấy sách '{order['book_title']}' để đặt."

    book_id, matched_title, stock = res

    if order["quantity"] > stock:
        conn.close()
        return f"Sách '{matched_title}' chỉ còn {stock} quyển, không đủ số lượng {order['quantity']}."

    cursor.execute("""
        INSERT INTO orders (customer_name, phone, address, book_id, quantity, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (customer_name, order["phone"], order["address"], book_id, order["quantity"], "pending"))
    conn.commit()
    conn.close()

    return f"Đơn hàng {order['quantity']} quyển '{matched_title}' đã được ghi nhận, giao tới {order['address']}."


pending_order = None
def process_user_input(user_input: str):
    global pending_order
    if pending_order is not None:
        customer_name = user_input.strip()
        result = place_order(pending_order, customer_name)
        pending_order = None
        return result

    intent = classify_intent(user_input)
    print(f"Intent: {intent}")

    if intent == "detail_book":
        book_title = extract_book_title(user_input)
        result = lookup_book(book_title)
    elif intent == "place_order":
        order = extract_order_entities(user_input)
        pending_order = order
        result = f"Bạn vui lòng cho mình biết tên khách hàng để hoàn tất đơn {order['quantity']} quyển '{order['book_title']}'?"

    else:
        result = "Không nhận diện được intent."

    return result


if __name__ == "__main__":
    while True:
        user_input = input("Bạn: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = process_user_input(user_input)
        print("Bot:", response)
