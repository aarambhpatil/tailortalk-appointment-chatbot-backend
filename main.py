# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from agent import app_runnable

app = FastAPI(
    title="TailorTalk Agent Server",
    description="An API server for the conversational booking agent.",
)

class ChatRequest(BaseModel):
    query: str
    history: list = [] 

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    conversation_history = [HumanMessage(content=request.query)]
    response = app_runnable.invoke({"messages": conversation_history})
    final_response = response['messages'][-1].content
    
    return {"response": final_response}

@app.get("/")
def read_root():
    return {"message": "TailorTalk Agent is running."}