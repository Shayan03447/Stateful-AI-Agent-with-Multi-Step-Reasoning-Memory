"""
LangGraph Database Backend
A conversational chatbot backend with persistent SQLite database storage.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3
import os

# Load environment variables
load_dotenv()

# Initialize the OpenAI model
model = ChatOpenAI(
    model_name='gpt-3.5-turbo',
    temperature=0.7,
    openai_api_key=os.getenv('OPENAI_API_KEY')
)

#------------------------------State Definition------------------------
class ChatState(TypedDict):
    """Chat state containing message history."""
    messages: Annotated[list[BaseMessage], add_messages]

#------------------------------Node Functions------------------------
def chat_node(state: ChatState) -> dict:
    """
    Process user messages and generate AI response.
    
    Args:
        state: Current chat state containing messages
        
    Returns:
        Dictionary with AI response message
    """
    response = model.invoke(state['messages'])
    return {'messages': [response]}

#-------------------------------Graph Construction-------------------------
graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

#--------------------------------Database Connection-------------------
# Create database directory if it doesn't exist
db_dir = 'data'
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, 'chatbot_db.sqlite')

try:
    conn = sqlite3.connect(database=db_path, check_same_thread=False)
except Exception as e:
    raise ConnectionError(f"Failed to connect to database: {e}")

#-------------------------------Checkpoint Configuration------------------------
checkpoint = SqliteSaver(conn=conn)

#-------------------------------Compile Graph-----------------------------
chatbot = graph.compile(checkpointer=checkpoint)

#------------------------------Utility Functions------------------------
def retrieve_all_thread():
    """
    Retrieve all conversation thread IDs from the database.
    
    Returns:
        List of thread IDs (UUIDs as strings)
    """
    try:
        all_threads = set()
        for cp in checkpoint.list(None):
            thread_id = cp.config.get('configurable', {}).get('thread_id')
            if thread_id:
                all_threads.add(thread_id)
        return list(all_threads)
    except Exception as e:
        print(f"Error retrieving threads: {e}")
        return []

def delete_thread(thread_id: str) -> bool:
    """
    Delete a conversation thread from the database.
    
    Args:
        thread_id: UUID of the thread to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Note: SqliteSaver doesn't have a direct delete method
        # This would require custom implementation or using raw SQL
        # For now, we'll return False and handle deletion differently
        return False
    except Exception as e:
        print(f"Error deleting thread: {e}")
        return False