import mysql.connector
import json
import joblib
import re
import logging
from typing import Dict, Optional, Tuple
from contextlib import contextmanager
from sentence_transformers import SentenceTransformer
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import Ollama
from fuzzywuzzy import process

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------
# Configuration
# ------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "17101975",  # Consider using environment variables
    "database": "bookstore"
}

FUZZY_MATCH_THRESHOLD = 70
DEFAULT_CUSTOMER_NAME = "Khách hàng"

# ------------------------
# 1. Load models with error handling
# ------------------------
try:
    embed_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    clf = joblib.load("model/model_xgb.pkl")
    label_encoder = joblib.load("model/label_encoder.pkl")
    logger.info("Models loaded successfully")
except Exception as e:
    logger.error(f"Error loading models: {e}")
    raise


def classify_intent(user_input: str) -> str:
    """Classify user intent using pre-trained model."""
    try:
        emb = embed_model.encode([user_input])
        pred_label = clf.predict(emb)[0]
        intent = label_encoder.inverse_transform([pred_label])[0]
        return intent
    except Exception as e:
        logger.error(f"Error classifying intent: {e}")
        return "unknown"


# ------------------------
# 2. Improved database connection with context manager
# ------------------------
@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        yield conn
    except mysql.connector.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


# ------------------------
# 3. Improved book lookup
# ------------------------
def extract_book_title(user_input: str) -> str:
    """Extract book title from user input using improved regex."""
    patterns = [
        r'(?:cuốn|quyển|sách)?\s*(.+?)(?:\s*(?:giá|còn|tập|thông tin|,|$))',
        r'(.+?)(?:\s*(?:như thế nào|ra sao|bao nhiêu|$))',
        r'(?:tìm|xem|kiếm)\s+(.+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, user_input.strip(), re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            if title and len(title) > 1:
                return title

    return user_input.strip()


def lookup_book(book_title: str) -> str:
    """Look up book information in database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT title, author, price, stock, category 
                FROM books 
                WHERE title LIKE %s 
                ORDER BY title
            """
            cursor.execute(query, (f"%{book_title}%",))
            results = cursor.fetchall()

            if results:
                responses = []
                for title, author, price, stock, category in results:
                    stock_status = "còn hàng" if stock > 0 else "hết hàng"
                    response = (f"📚 {title}\n"
                                f"   Tác giả: {author}\n"
                                f"   Giá: {price:,.0f} VNĐ\n"
                                f"   Tồn kho: {stock} quyển ({stock_status})\n"
                                f"   Thể loại: {category}\n")
                    responses.append(response)
                return "\n".join(responses)
            else:
                return f"❌ Không tìm thấy sách với từ khóa '{book_title}'."

    except Exception as e:
        logger.error(f"Error looking up book: {e}")
        return "Lỗi khi tìm kiếm sách. Vui lòng thử lại."


# ------------------------
# 4. Enhanced LLM entity extraction
# ------------------------
llm = Ollama(model="llama3.2:1b")
entity_prompt = PromptTemplate(
    input_variables=["user_input"],
    template="""Trích xuất thông tin đặt hàng từ câu sau và trả về JSON:
{{"book_title": "tên sách", "quantity": số_lượng, "address": "địa chỉ", "phone": "số điện thoại"}}

Câu: {user_input}

JSON:"""
)
entity_chain = LLMChain(llm=llm, prompt=entity_prompt)


def extract_order_entities(user_input: str) -> Dict[str, any]:
    """Extract order entities using LLM with regex fallback."""
    try:
        # Try LLM extraction first
        response = entity_chain.invoke({"user_input": user_input})
        json_str = response["text"] if isinstance(response, dict) else response

        # Clean the response
        json_str = json_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]

        order = json.loads(json_str)

        # Validate and clean extracted data
        return {
            "book_title": str(order.get("book_title") or "").strip().rstrip(",."),
            "quantity": max(1, int(order.get("quantity") or 1)),
            "address": str(order.get("address") or "Unknown").strip().rstrip(",."),
            "phone": str(order.get("phone") or "Unknown").strip().rstrip(",.")
        }

    except Exception as e:
        logger.warning(f"LLM extraction failed: {e}, falling back to regex")
        return extract_order_entities_regex(user_input)


def extract_order_entities_regex(user_input: str) -> Dict[str, any]:
    """Fallback regex-based entity extraction."""
    # Extract phone number
    phone_patterns = [
        r'(?:số điện thoại|sđt|đt|phone)[:\s]*([\d\s\-]{8,15})',
        r'(\b(?:0[1-9]|84[1-9])[\d\s\-]{7,11}\b)'
    ]
    phone = "Unknown"
    for pattern in phone_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            phone = re.sub(r'[\s\-]', '', match.group(1))
            break

    # Remove phone from input for cleaner address extraction
    temp_input = user_input
    for pattern in phone_patterns:
        temp_input = re.sub(pattern, '', temp_input, flags=re.IGNORECASE)

    # Extract address
    addr_patterns = [
        r'(?:giao|tới|đến|về|địa chỉ|ở)\s+([^,\d]*(?:[^\d,]*[a-zA-Zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệđìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ][^,]*)*)',
        r'([a-zA-Zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệđìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ\s,]+(?:quận|huyện|phường|xã|thành phố|tỉnh)[^,]*)'
    ]
    address = "Unknown"
    for pattern in addr_patterns:
        match = re.search(pattern, temp_input, re.IGNORECASE)
        if match:
            address = match.group(1).strip().rstrip(",.")
            break

    # Extract quantity
    qty_match = re.search(r'(\d+)\s*(?:cuốn|quyển|bản|cái)?', user_input, re.IGNORECASE)
    quantity = int(qty_match.group(1)) if qty_match else 1

    # Extract book title
    book_patterns = [
        r'(?:mua|đặt|order)\s*(?:\d+)?\s*(?:cuốn|quyển)?\s*(.+?)(?=\s*(?:giao|tới|đến|về|địa chỉ|số điện thoại)|$)',
        r'(?:cuốn|quyển|sách)\s+(.+?)(?=\s*(?:giao|tới|đến|về)|$)',
        r'^(.+?)(?=\s*(?:\d+\s*(?:cuốn|quyển))|(?:giao|tới|đến)|$)'
    ]
    book_title = "Unknown"
    for pattern in book_patterns:
        match = re.search(pattern, temp_input.strip(), re.IGNORECASE)
        if match:
            title = match.group(1).strip().rstrip(",.")
            if title and len(title) > 2:
                book_title = title
                break

    return {
        "book_title": book_title,
        "quantity": quantity,
        "address": address,
        "phone": phone
    }


# ------------------------
# 5. Enhanced order placement
# ------------------------
def find_book_by_title(cursor, book_title: str) -> Optional[Tuple]:
    """Find book using exact match, fuzzy matching, and partial matching."""
    # 1. Exact match (case insensitive)
    cursor.execute(
        "SELECT book_id, title, stock, price FROM books WHERE LOWER(title) = LOWER(%s)",
        (book_title,)
    )
    result = cursor.fetchone()
    if result:
        return result, 100  # Perfect match score

    # 2. Partial match with LIKE
    cursor.execute(
        "SELECT book_id, title, stock, price FROM books WHERE LOWER(title) LIKE %s",
        (f"%{book_title.lower()}%",)
    )
    result = cursor.fetchone()
    if result:
        return result, 90  # High confidence

    # 3. Fuzzy matching
    cursor.execute("SELECT book_id, title, stock, price FROM books")
    all_books = cursor.fetchall()

    if all_books:
        titles = [book[1] for book in all_books]
        best_match, score = process.extractOne(book_title, titles)

        if score >= FUZZY_MATCH_THRESHOLD:
            for book in all_books:
                if book[1] == best_match:
                    return book, score

    return None, 0


def place_order(order: Dict[str, any], customer_name: str = DEFAULT_CUSTOMER_NAME) -> str:
    """Place an order with improved error handling and validation."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            book_title = order['book_title'].strip()
            if not book_title or book_title == "Unknown":
                return "❌ Không thể xác định tên sách. Vui lòng cung cấp tên sách cụ thể."

            # Find book
            book_info, confidence = find_book_by_title(cursor, book_title)
            if not book_info:
                return f"❌ Không tìm thấy sách '{book_title}' trong kho."

            book_id, matched_title, stock, price = book_info

            # Validate stock
            if order["quantity"] > stock:
                return (f"❌ Sách '{matched_title}' chỉ còn {stock} quyển, "
                        f"không đủ số lượng {order['quantity']} quyển yêu cầu.")

            # Validate required fields
            if order["address"] == "Unknown":
                return "❌ Vui lòng cung cấp địa chỉ giao hàng."

            if order["phone"] == "Unknown":
                return "❌ Vui lòng cung cấp số điện thoại liên hệ."

            # Calculate total
            total_amount = price * order["quantity"]

            # Insert order (without total_amount if column doesn't exist)
            cursor.execute("""
                INSERT INTO orders (customer_name, phone, address, book_id, quantity, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (customer_name, order["phone"], order["address"], book_id, order["quantity"], "pending"))

            # Update stock
            cursor.execute("""
                UPDATE books SET stock = stock - %s WHERE book_id = %s
            """, (order["quantity"], book_id))

            conn.commit()
            order_id = cursor.lastrowid

            # Generate success message
            confidence_msg = f" (độ khớp: {confidence}%)" if confidence < 100 else ""
            return (f"✅ Đơn hàng #{order_id} đã được tạo thành công!\n"
                    f"📚 Sách: {matched_title}{confidence_msg}\n"
                    f"📦 Số lượng: {order['quantity']} quyển\n"
                    f"💰 Tổng tiền: {total_amount:,.0f} VNĐ\n"
                    f"📍 Giao tới: {order['address']}\n"
                    f"📞 Liên hệ: {order['phone']}")

    except Exception as e:
        logger.error(f"Error placing order: {e}")
        return "❌ Lỗi khi đặt hàng. Vui lòng thử lại sau."


# ------------------------
# 6. Enhanced main pipeline
# ------------------------
def process_user_input(user_input: str, customer_name: str = DEFAULT_CUSTOMER_NAME) -> str:
    """Process user input through the chatbot pipeline."""
    if not user_input.strip():
        return "Vui lòng nhập câu hỏi hoặc yêu cầu của bạn."

    try:
        intent = classify_intent(user_input)
        logger.info(f"Detected intent: {intent} for input: {user_input}")

        if intent == "detail_book":
            book_title = extract_book_title(user_input)
            return lookup_book(book_title)

        elif intent == "place_order":
            order = extract_order_entities(user_input)
            return place_order(order, customer_name)

        else:
            return (f"🤔 Tôi chưa hiểu ý bạn (intent: {intent}). "
                    f"Bạn có thể hỏi về thông tin sách hoặc đặt hàng không?")

    except Exception as e:
        logger.error(f"Error processing user input: {e}")
        return "❌ Đã xảy ra lỗi. Vui lòng thử lại."


# ------------------------
# 7. Enhanced demo with better UX
# ------------------------
if __name__ == "__main__":
    print("🤖 Chào mừng đến với Chatbot Nhà Sách!")
    print("💡 Bạn có thể:")
    print("   - Hỏi thông tin sách: 'Sách Python có không?'")
    print("   - Đặt hàng: 'Mua 2 cuốn Python giao 123 ABC, sđt 0912345678'")
    print("   - Gõ 'exit' để thoát\n")

    while True:
        try:
            user_input = input("🧑 Bạn: ").strip()
            if user_input.lower() in ["exit", "quit", "thoát"]:
                print("👋 Cảm ơn bạn đã sử dụng dịch vụ!")
                break

            if not user_input:
                continue

            response = process_user_input(user_input)
            print(f"🤖 Bot: {response}\n")

        except KeyboardInterrupt:
            print("\n👋 Tạm biệt!")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print("❌ Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.")