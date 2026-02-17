"""
LangGraph Conversational Chatbot Frontend
A beautiful Streamlit UI for the database-backed conversational chatbot.
"""

import streamlit as st
from langgraph_database_backend import chatbot, retrieve_all_thread
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime
import time

#----------------------------Page Configuration-----------------------
st.set_page_config(
    page_title="LangGraph Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

#----------------------------Custom CSS Styling-----------------------
st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] .sidebar-content {
        color: white;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem;
        border-radius: 15px;
        margin-bottom: 1rem;
    }
    
    /* Thread button styling */
    .thread-button {
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .thread-button:hover {
        background-color: rgba(255, 255, 255, 0.2);
        transform: translateX(5px);
    }
    
    /* Title styling */
    h1 {
        color: #667eea;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

#----------------------------Utility Functions-----------------------
def generate_thread_id():
    """Generate a new unique thread ID."""
    return str(uuid.uuid4())

def reset_chat():
    """Reset the current chat session."""
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []
    st.session_state['conversation_titles'] = {}
    st.rerun()

def add_thread(thread_id):
    """Add a thread to the list if it doesn't exist."""
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    """Load conversation messages for a given thread ID."""
    try:
        state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
        return state.values.get('messages', [])
    except Exception as e:
        st.error(f"Error loading conversation: {e}")
        return []

def get_conversation_title(thread_id, messages):
    """Generate or retrieve a title for a conversation."""
    if thread_id in st.session_state.get('conversation_titles', {}):
        return st.session_state['conversation_titles'][thread_id]
    
    # Generate title from first user message
    if messages:
        first_user_msg = next((msg for msg in messages if isinstance(msg, HumanMessage)), None)
        if first_user_msg:
            title = first_user_msg.content[:50] + "..." if len(first_user_msg.content) > 50 else first_user_msg.content
            if 'conversation_titles' not in st.session_state:
                st.session_state['conversation_titles'] = {}
            st.session_state['conversation_titles'][thread_id] = title
            return title
    
    return f"Conversation {str(thread_id)[:8]}"

def format_thread_display(thread_id):
    """Format thread ID for display."""
    messages = load_conversation(thread_id)
    title = get_conversation_title(thread_id, messages)
    return title

#------------------------------------Session Setup--------------------------------
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    try:
        st.session_state['chat_threads'] = retrieve_all_thread()
    except Exception as e:
        st.error(f"Error loading threads: {e}")
        st.session_state['chat_threads'] = []

if 'conversation_titles' not in st.session_state:
    st.session_state['conversation_titles'] = {}

add_thread(st.session_state['thread_id'])

#-------------------------------------Sidebar UI-------------------------------
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: white; margin: 0;'>💬 LangGraph</h1>
            <p style='color: rgba(255,255,255,0.8); margin: 0;'>Conversational AI</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # New Chat Button
    if st.button("✨ New Chat", use_container_width=True, type="primary"):
        reset_chat()
    
    st.markdown("---")
    
    # Conversation History
    st.markdown("### 📚 Conversation History")
    
    if not st.session_state['chat_threads']:
        st.info("No conversations yet. Start a new chat!")
    else:
        # Display threads in reverse order (newest first)
        for idx, thread_id in enumerate(reversed(st.session_state['chat_threads'])):
            # Use a unique key for each button
            button_key = f"thread_{thread_id}_{idx}"
            
            # Check if this thread is currently active
            is_active = thread_id == st.session_state['thread_id']
            
            # Get conversation title
            messages = load_conversation(thread_id)
            title = get_conversation_title(thread_id, messages)
            
            # Style active thread differently
            button_style = "primary" if is_active else "secondary"
            
            if st.button(
                f"{'📍 ' if is_active else '💭 '}{title}",
                key=button_key,
                use_container_width=True,
                type=button_style
            ):
                st.session_state['thread_id'] = thread_id
                messages = load_conversation(thread_id=thread_id)
                
                temp_messages = []
                for message in messages:
                    if isinstance(message, HumanMessage):
                        role = 'user'
                    elif isinstance(message, AIMessage):
                        role = 'assistant'
                    else:
                        role = 'assistant'
                    temp_messages.append({
                        'role': role,
                        'content': message.content
                    })
                st.session_state['message_history'] = temp_messages
                st.rerun()

#-------------------------------------Main Content Area-------------------------------
st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                   -webkit-background-clip: text; 
                   -webkit-text-fill-color: transparent;
                   font-size: 3rem;
                   margin: 0;'>🤖 AI Chatbot</h1>
        <p style='color: #666; font-size: 1.1rem;'>Powered by LangGraph & OpenAI</p>
    </div>
""", unsafe_allow_html=True)

#-------------------------------------Load Chat History--------------------------
if not st.session_state['message_history']:
    st.markdown("""
        <div style='text-align: center; padding: 3rem; color: #999;'>
            <h2>👋 Welcome!</h2>
            <p>Start a conversation by typing a message below.</p>
            <p>Your conversations are automatically saved and can be accessed from the sidebar.</p>
        </div>
    """, unsafe_allow_html=True)
else:
    for message in st.session_state['message_history']:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

#--------------------------------------Configuration--------------------------
CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

#-----------------------------------User Input--------------------------
user_input = st.chat_input("💬 Type your message here...")

if user_input:
    # Add user message to history
    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })
    
    # Display user message
    with st.chat_message('user'):
        st.markdown(user_input)
    
    # Generate and display AI response
    with st.chat_message('assistant'):
        try:
            # Collect streamed content
            ai_message_parts = []
            message_placeholder = st.empty()
            
            # Stream the response
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages'
            ):
                if hasattr(message_chunk, 'content') and message_chunk.content:
                    ai_message_parts.append(message_chunk.content)
                    # Update the placeholder with accumulated content
                    message_placeholder.markdown(''.join(ai_message_parts))
            
            # Get the full AI message
            ai_message = ''.join(ai_message_parts)
            
            # Update the final message display
            message_placeholder.markdown(ai_message)
            
            # Add AI message to history
            st.session_state['message_history'].append({
                'role': 'assistant',
                'content': ai_message
            })
            
            # Update conversation title if this is the first message
            if len(st.session_state['message_history']) == 2:
                thread_id = st.session_state['thread_id']
                if thread_id not in st.session_state['conversation_titles']:
                    title = user_input[:50] + "..." if len(user_input) > 50 else user_input
                    st.session_state['conversation_titles'][thread_id] = title
                    
        except Exception as e:
            st.error(f"Error generating response: {e}")
            st.info("Please check your OpenAI API key and try again.")
            # Remove the user message from history if there was an error
            if st.session_state['message_history'] and st.session_state['message_history'][-1]['role'] == 'user':
                st.session_state['message_history'].pop()