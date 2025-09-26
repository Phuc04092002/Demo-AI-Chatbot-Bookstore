Cách chạy demo chatbot:
- File code chatbot là Chatbot_demo.py
- Cài đặt các thư viện yêu cầu trong requirement.txt
- Import file SQL trong folder mySQL_DB_file vào MySQL
- Kết nối tới MySQL trong file Chatbot_demo.py
- Mở terminal trong project, chạy lệnh streamlit run UI_demo để chạy demo với Streamlit.
- Mở terminal và run UI_demo_(Gradio).py để chạy demo với Gradio


Một số vấn đề có thể cải thiện của chatbot hiện tại:
- Tập dữ liệu huấn luyện xác định yêu cầu lớn hơn, đa dạng hơn sẽ giúp mô hình xác định mục đích của yêu cầu chính xác hơn
- Có thể dùng các LLM có số tham số lớn hơn thay vì Llama 3.2 1B để extract information thành file JSON chính xác và đúng ý hơn, bù lại chatbot sẽ triển khai chậm hơn
- Hiện tại cách trả lời của chatbot vẫn khá cứng nhắc. Có thể sử dụng một LLM để generative câu trả lời cho người dùng dựa trên thông tin được cung cấp (tương tự như RAG), cách trả lời sẽ chuyên nghiệp và đúng trọng tâm hơn.
- Tìm kiếm bằng LIKE và fuzzy với database to sẽ khá chậm. Có thể tìm kiếm bằng semantic search, sử dụng FAISS
- Status hiện tại vẫn để tạm thời là Pending, và chỉ có 1 biến pending_order. Nếu người dùng nhập nhiều câu xen kẽ sẽ lỗi
- Mới chỉ có tương tác truy xuất và thêm thông tin vào database, chưa có các tương tác đa dạng hơn với database (như khi có đơn đặt thì số lượng còn lại của sách sẽ giảm đi)
- Xử lý lấy thông tin bằng regex vẫn còn cồng kềnh và cứng nhắc, tuy điều này chỉ là phụ trợ cho LLM extract information nhưng vẫn rất cần thiết để tránh truy xuất sai thông tin, đặc biệt là thông tin khách hàng khi có đơn đặt hàng.
