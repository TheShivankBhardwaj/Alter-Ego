import streamlit as st
from persona_chatbot_web import PersonaBot

# Set the page configuration
st.set_page_config(page_title="Alter-Ego Chat", page_icon="🤖")

# Title of the app
st.title("🤖 Alter-Ego Chatbot")

# Sidebar for persona selection
with st.sidebar:
    st.header("Pick Your Persona")
    name_input = st.text_input("Name (e.g., Elon Musk)", value=st.session_state.get("persona_name", ""))
    occupation_input = st.text_input("Occupation (optional, e.g., Entrepreneur)", value=st.session_state.get("persona_occupation", ""))
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

# Initialize session state for messages
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "bot" not in st.session_state:
    st.session_state.bot = None
if "persona_name" not in st.session_state:
    st.session_state.persona_name = ""
if "persona_occupation" not in st.session_state:
    st.session_state.persona_occupation = ""

# Display chat history
if st.session_state.bot:
    st.subheader(f"Chatting with {st.session_state.persona_name}" + 
                 (f" ({st.session_state.persona_occupation})" if st.session_state.persona_occupation else ""))
    
    for message in st.session_state.chat_history:
        role = message.get("role", "assistant" if message.get(st.session_state.persona_name) else "user")
        content = message.get("content", message.get("user", message.get(st.session_state.persona_name, "")))
        with st.chat_message(role):
            st.markdown(content)

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Append user message to session state
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate persona response
        with st.chat_message(st.session_state.persona_name):
            message_placeholder = st.empty()
            full_response = ""

            # Simulate streaming effect (single response split into chunks)
            try:
                reply = st.session_state.bot.chat(prompt)
                # Break reply into chunks for placeholder effect
                for i in range(0, len(reply), 10):  # Adjust chunk size (10 chars) for speed
                    chunk = reply[i:i + 10]
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                    # Small delay hack for visual effect
                    st.session_state._counter = getattr(st.session_state, "_counter", 0) + 1
                message_placeholder.markdown(full_response)
            except Exception as e:
                message_placeholder.error(f"Error: {e}")

        # Append persona response to session state
        st.session_state.chat_history.append({"role": st.session_state.persona_name, "content": full_response})

    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()
else:
    st.info("Enter a name in the sidebar to start chatting!")