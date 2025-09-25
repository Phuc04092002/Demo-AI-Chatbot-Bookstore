import streamlit as st
from Run_model_demo.Chatbot_demo import process_user_input

st.title("Chatbot BookStore Demo")

if "pending_order" not in st.session_state:
    st.session_state.pending_order = None

user_input = st.text_input("Bạn:", "")

if user_input:
    response = process_user_input(user_input)
    st.text_area("Bot:", value=response, height=200)
