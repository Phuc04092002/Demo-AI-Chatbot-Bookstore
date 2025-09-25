import ollama

def clean_intent(raw: str) -> str:
    raw = raw.strip().lower().replace("(", "").replace(")", "").replace(".", "")
    return raw.split()[0]

def classify_intent(user_input: str) -> str:
    prompt = f"""
Bạn là bộ phân loại intent cho chatbot BookStore.
Người dùng có thể:
1. Tra cứu thông tin sách → 'detail_book'
2. Đặt mua sách → 'place_order'

Chỉ trả về một từ: 'detail_book' hoặc 'place_order'.
KHÔNG giải thích, KHÔNG bình luận, KHÔNG dấu chấm, KHÔNG ngoặc.

Câu người dùng: "{user_input}"
"""
    response = ollama.chat(
        model="llama3.2:1b",
        messages=[{"role": "user", "content": prompt}]
    )
    return clean_intent(response["message"]["content"])

# Test
print(classify_intent("Tôi muốn mua 2 quyển Naruto tập 20, giao tới Hà Nội, số 0909xxx"))

# print(classify_intent("Có sách Naruto không?"))
