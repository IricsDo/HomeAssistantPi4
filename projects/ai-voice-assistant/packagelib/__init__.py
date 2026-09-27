import os
import nltk 
import pyttsx3
import getpass
import assemblyai as aai
import speech_recognition as sr
#------------------------------#
from gtts import gTTS
from pydantic import Field
from nltk.util import ngrams
from nltk.corpus import words
from dotenv import load_dotenv
from spellchecker import SpellChecker
from langchain_core.tools import tool
from gingerit import GingerIt # Not using for now, but will be defined first
from nltk.metrics.distance import jaccard_distance
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


load_dotenv()
aai.settings.api_key = os.getenv("Assembly_AI_KEY")