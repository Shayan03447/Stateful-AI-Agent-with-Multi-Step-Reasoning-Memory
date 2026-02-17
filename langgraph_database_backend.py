   
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3

load_dotenv()
model=ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.7)

#------------------------------State------------------------

class ChatState(TypedDict):
    messages: Annotated[list, add_messages]

#------------------------------Node------------------------
def chat_node(state: ChatState):
    response=model.invoke(state['messages'])
    return {'messages':[response]}

#-------------------------------Graph-------------------------
graph=StateGraph(ChatState)
graph.add_node('chat_node', chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

#--------------------------------DB Connection-------------------
conn = sqlite3.connect(databse='chatbot_db', check_same_thread=False)

#-------------------------------CheckPoint------------------------

checkpoint=SqliteSaver(conn=conn)

#-------------------------------compile-----------------------------
chatbot=graph.compile(checkpointer=checkpoint)

def retrieve_all_thread():
    all_threads=set()
    for cp in checkpoint.list(None):
        all_threads.add(cp.config['configurable']['thread_id'])
    return list(all_threads)

            