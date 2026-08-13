from langchain_core.messages import HumanMessage, AIMessage


class ChatMemory:

    def __init__(self, max_messages=10):
        self.messages = []
        self.max_messages = max_messages

    def add_user_message(self, message):
        self.messages.append(
            HumanMessage(content=message)
        )
        self._trim()

    def add_ai_message(self, message):
        self.messages.append(
            AIMessage(content=message)
        )
        self._trim()

    def get_history(self):
        return self.messages.copy()

    def clear(self):
        self.messages.clear()

    def _trim(self):
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]