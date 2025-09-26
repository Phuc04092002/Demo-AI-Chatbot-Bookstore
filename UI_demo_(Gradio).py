import gradio as gr
from Chatbot_demo import process_user_input


# Hàm xử lý hội thoại với Gradio
def chatbot_ui(user_input, history):
    # Gọi lại hàm chatbot bạn đã viết
    response = process_user_input(user_input)
    # history là list [(user, bot), ...]
    history.append((user_input, response))
    return history, history


with gr.Blocks() as demo:
    gr.Markdown("## 📚 Chatbot Bookstore Demo")

    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="Nhập tin nhắn...")
    clear = gr.Button("Clear")

    state = gr.State([])  # lưu lịch sử hội thoại

    msg.submit(chatbot_ui, [msg, state], [chatbot, state])
    clear.click(lambda: ([], []), None, [chatbot, state])

if __name__ == "__main__":
    demo.launch(share = True)