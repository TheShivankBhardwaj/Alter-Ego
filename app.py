import streamlit as st
from persona_chatbot_web import PersonaBot

st.set_page_config(page_title="GenAI Persona Chat", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f6f5; padding: 20px; }
    .stTextInput > div > div > input {
        border-radius: 20px; padding: 10px; border: 1px solid #ccc; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton > button {
        border-radius: 20px; padding: 8px 20px; background: linear-gradient(90deg, #ff7f0e, #ff5733);
        color: white; border: none; font-weight: bold; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .stButton > button:hover { background: linear-gradient(90deg, #ff5733, #ff7f0e); }
    .sidebar .sidebar-content { background: linear-gradient(135deg, #1f77b4, #3498db); padding: 20px; color: white; }
    .sidebar .stTextInput > div > div > input { background-color: rgba(255, 255, 255, 0.9); }
    .sidebar .stButton > button { background: #ff7f0e; }
    .chat-container { max-height: 70vh; overflow-y: auto; padding: 20px; background: white; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .chat-you { 
        background: #1f77b4; color: white; padding: 10px 15px; border-radius: 15px 15px 0 15px; 
        margin: 10px 50px 10px 0; max-width: 70%; word-wrap: break-word; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .chat-bot { 
        background: #ff7f0e; color: white; padding: 10px 15px; border-radius: 15px 15px 15px 0; 
        margin: 10px 0 10px 50px; max-width: 70%; word-wrap: break-word; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .input-container { position: fixed; bottom: 20px; width: 90%; max-width: 800px; display: flex; gap: 10px; }
    h1 { color: #333; font-family: 'Arial', sans-serif; text-align: center; }
    h3 { color: #555; font-family: 'Arial', sans-serif; }
    </style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "bot" not in st.session_state:
    st.session_state.bot = None
if "persona_name" not in st.session_state:
    st.session_state.persona_name = ""
if "persona_occupation" not in st.session_state:
    st.session_state.persona_occupation = ""

st.title("Alter-Ego Chatbot")

with st.sidebar:
    st.header("Pick Your Persona")
    name_input = st.text_input("Name (e.g., Elon Musk)", value=st.session_state.persona_name)
    occupation_input = st.text_input("Occupation (optional, e.g., Entrepreneur)", value=st.session_state.persona_occupation)
    if st.button("Set Persona"):
        if name_input:
            with st.spinner(f"Loading {name_input}'s persona..."):
                try:
                    st.session_state.bot = PersonaBot(name_input, occupation_input)
                    st.session_state.persona_name = name_input
                    st.session_state.persona_occupation = occupation_input
                    st.session_state.chat_history = []
                    st.success(f"Ready to chat with {name_input}!")
                except Exception as e:
                    st.error(f"Oops: {e}")
        else:
            st.warning("Enter a name first!")

if st.session_state.bot:
    st.subheader(f"Chatting with {st.session_state.persona_name}" + 
                 (f" ({st.session_state.persona_occupation})" if st.session_state.persona_occupation else ""))

    chat_container = st.container()
    with chat_container:
        for speaker, message in st.session_state.chat_history:
            if speaker == "You":
                st.markdown(f"<div class='chat-you'>{message}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-bot'>{message}</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='input-container'>", unsafe_allow_html=True)
        user_input = st.text_input("Type your message:", key="user_input", placeholder="Ask me anything...", label_visibility="collapsed")
        send_button = st.button("Send")
        st.markdown("</div>", unsafe_allow_html=True)

        if send_button and user_input:
            st.session_state.chat_history.append(("You", user_input))
            with st.spinner(f"{st.session_state.persona_name} is typing..."):
                reply = st.session_state.bot.chat(user_input)
                st.session_state.chat_history.append((st.session_state.persona_name, reply))
            st.rerun()

    if st.button("Clear Chat", key="clear"):
        st.session_state.chat_history = []
        st.rerun()
else:
    st.info("Enter a name in the sidebar to start chatting!")