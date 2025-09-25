import csv
import random

# Danh sách mẫu sách
books = [
    "Harry Potter và Hòn đá Phù thủy",
    "Đắc Nhân Tâm",
    "Tuổi Trẻ Đáng Giá Bao Nhiêu",
    "Sherlock Holmes Toàn Tập",
    "Nhà Giả Kim",
    "Sapiens: Lược Sử Loài Người",
    "Totto-chan Bên Cửa Sổ",
    "Dế Mèn Phiêu Lưu Ký",
    "Không Gia Đình",
    "Hoàng Tử Bé",
    "One Piece tập 10",
    "Naruto tập 20",
    "Không gia đình",
    "Tuyển tập thơ mùa hạ",
    "Đàn ông sao Hỏa đàn bà sao Kim"
]

# Địa chỉ và số điện thoại mẫu
addresses = [
    "123 Nguyễn Trãi, Hà Nội",
    "45 Lê Lợi, TP.HCM",
    "78 Trần Phú, Đà Nẵng",
    "56 Hai Bà Trưng, Hải Phòng",
    "99 Phan Chu Trinh, Huế"
]

phones = [
    "0912345678",
    "0987654321",
    "0909123456",
    "0978123456",
    "0934567890"
]

# Mẫu câu đặt hàng đa dạng
order_templates = [
    "Tôi muốn đặt {qty} cuốn '{book}', giao đến {addr}, liên hệ {phone}.",
    "Làm ơn gửi cho tôi {qty} bản '{book}' đến địa chỉ {addr}, số điện thoại {phone}.",
    "Đặt {qty} quyển '{book}' giúp tôi, ship tới {addr}, liên lạc qua {phone}.",
    "Tôi cần mua {qty} cuốn '{book}', xin giao tới {addr}, gọi {phone} khi đến.",
    "Hãy gửi {qty} quyển '{book}' cho tôi, địa chỉ {addr}, số {phone}."
]

# Mẫu câu hỏi chi tiết đa dạng
question_templates = [
    "Cho tôi hỏi sách '{book}' có bao nhiêu trang?",
    "Ai là tác giả của '{book}' vậy?",
    "Giá bán hiện tại của '{book}' là bao nhiêu?",
    "'{book}' có bản bìa cứng không?",
    "Tôi muốn biết '{book}' có ebook không?",
    "Nhà xuất bản nào phát hành '{book}'?",
    "'{book}' xuất bản năm nào?",
    "Sách '{book}' phù hợp cho độ tuổi nào?",
    "'{book}' có phải bản dịch mới nhất không?",
    "Cửa hàng còn hàng '{book}' không?",
    "Bạn có thể tóm tắt nội dung '{book}' cho tôi không?",
    "'{book}' có được giải thưởng nào không?",
    "Có bản tiếng Anh của '{book}' không?",
    "Thời gian giao '{book}' thường mất bao lâu?",
    "Có thể xem mục lục của '{book}' không?"
]

rows = []

# Sinh 500 place_order
for _ in range(500):
    book = random.choice(books)
    qty = random.randint(1, 5)
    addr = random.choice(addresses)
    phone = random.choice(phones)
    template = random.choice(order_templates)
    text = template.format(qty=qty, book=book, addr=addr, phone=phone)
    rows.append([ text, "place_order"])

# Sinh 500 detail_book
for _ in range(500):
    book = random.choice(books)
    template = random.choice(question_templates)
    text = template.format(book=book)
    rows.append([text, "detail_book"])

# Trộn dữ liệu
random.shuffle(rows)

# Ghi ra file CSV
with open("bookstore_requests_balanced.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["text","label"])
    writer.writerows(rows)

print("File bookstore_requests_balanced.csv đã được tạo thành công.")
