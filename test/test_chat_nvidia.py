from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import getpass
import os
from dotenv import load_dotenv

load_dotenv()


from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain_core.tools import tool
from pydantic import Field

tool_models = [
    model for model in ChatNVIDIA.get_available_models() if model.supports_tools
]

# The function name, type hints, and docstring are all part of the tool
# schema that's passed to the model. Defining good, descriptive schemas
# is an extension of prompt engineering and is an important part of
# getting models to perform well.
@tool
def add(a: int, b: int) -> int:
    """Add two integers.

    Args:
        a: First integer
        b: Second integer
    """
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers.

    Args:
        a: First integer
        b: Second integer
    """
    return a * b

tools = [add, multiply]

llm = ChatNVIDIA(model=tool_models[0].id).bind_tools(tools=tools)
response = llm.invoke("What is 3 * 12? Also, what is 11 + 49?")
print(response.content)

#########################################################
# from langchain_core.prompts import ChatPromptTemplate

# prompt = ChatPromptTemplate(
#     [
#         (
#             "system",
#             "You are a helpful assistant that translates {input_language} to {output_language}.",
#         ),
#         ("human", "{input}"),
#     ]
# )

# chain = prompt | llm
# chain.invoke(
#     {
#         "input_language": "English",
#         "output_language": "German",
#         "input": "I love programming.",
#     }
# )

###########################################################################
# # store is a dictionary that maps session IDs to their corresponding chat histories.
# store = {}  # memory is maintained outside the chain


# # A function that returns the chat history for a given session ID.
# def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
#     if session_id not in store:
#         store[session_id] = InMemoryChatMessageHistory()
#     return store[session_id]


# chat = ChatNVIDIA(
#     model="mistralai/mixtral-8x22b-instruct-v0.1",
#     temperature=0.1,
#     max_tokens=100,
#     top_p=1.0,
# )

# #  Define a RunnableConfig object, with a `configurable` key. session_id determines thread
# config = {"configurable": {"session_id": "1"}}

# conversation = RunnableWithMessageHistory(
#     chat,
#     get_session_history,
# )

# result = conversation.invoke(
#     "Hi I'm Srijan Dubey.",  # input or query
#     config=config,
# )

# print(result.content)

# conversation.invoke(
#     "I'm doing well! Just having a conversation with an AI.",
#     config=config,
# )

# conversation.invoke(
#     "Tell me about yourself.",
#     config=config,
# )
#####################################################################
# client = ChatNVIDIA(
#   model="mistralai/mixtral-8x22b-instruct-v0.1",
#   api_key=os.getenv('NVIDIA_API_KEY'), 
#   temperature=0.2,
#   top_p=0.7,
#   max_tokens=1024,
# )

# result = client.invoke("Write a ballad about LangChain.")
# print(result.content)

#####################################################################################
# prompt = ChatPromptTemplate.from_messages(
#     [("system", "You are a helpful AI assistant named Fred."), ("user", "{input}")]
# )
# chain = prompt | ChatNVIDIA(model="meta/llama3-8b-instruct") | StrOutputParser()

# for txt in chain.stream({"input": "What's your name?"}):
#     print(txt, end="")