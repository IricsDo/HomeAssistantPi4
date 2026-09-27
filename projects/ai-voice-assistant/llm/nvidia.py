from packagelib import *
from utilities.prompt_template import SYSTEM_PROMPT

class VoiceAssistant:
    def __init__(self) -> None:
        # Define chat model and prompt
        self.__CHAT = ChatNVIDIA(
            model="meta/llama3-8b-instruct",
            temperature=0.1,
            max_tokens=100,
            top_p=1.0,
        )
        self.__PROMPT = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("user", "{user_input}"),
            ]
        )

        #  Define a RunnableConfig object, with a `configurable` key. session_id determines thread
        self.MY_CONFIG = {"configurable": {"session_id": "my_assistant"}}
        self.__CHAIN = self.__PROMPT | self.__CHAT
        self.CONVERSATION = RunnableWithMessageHistory(
            self.__CHAIN,
            self.get_session_history,
            input_messages_key="user_input",
            history_messages_key="chat_history",
        )
        # store is a dictionary that maps session IDs to their corresponding chat histories.
        self.__STORE_HISSTORY = {}  # memory is maintained outside the chain

    # A function that returns the chat history for a given session ID.
    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self.__STORE_HISSTORY:
            self.__STORE_HISSTORY[session_id] = InMemoryChatMessageHistory()
        return self.__STORE_HISSTORY[session_id]