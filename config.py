# config.py
import os
import getpass
from dotenv import load_dotenv, find_dotenv
from langchain_gigachat.embeddings.gigachat import GigaChatEmbeddings

load_dotenv(find_dotenv())

if "AUTH_KEY" not in os.environ:
    os.environ["AUTH_KEY"] = getpass.getpass("Введите ключ авторизации GigaChat API: ")

if "AUTH_URL" not in os.environ:
    os.environ["AUTH_URL"] = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    
if "GIGA_URL" not in os.environ:
    os.environ["GIGA_URL"] = "https://gigachat.devices.sberbank.ru/api/v1"

if "MODEL_TYPE" not in os.environ:
    os.environ["MODEL_TYPE"] = "GigaChat-Max"  # Default model

AUTH_KEY = os.environ["AUTH_KEY"]
AUTH_URL = os.environ["AUTH_URL"]
GIGA_URL = os.environ['GIGA_URL']
MODEL_TYPE = os.environ["MODEL_TYPE"]  # GigaChat, GigaChat-Pro, or GigaChat-Max
PORT = int(os.environ.get("PORT", 8080))

from langchain_gigachat.chat_models import GigaChat

llm = GigaChat(
    credentials=AUTH_KEY,
    scope="GIGACHAT_API_PERS",
    model=MODEL_TYPE,
    verify_ssl_certs=False,
    auth_url=AUTH_URL,
    base_url=GIGA_URL,
    timeout=300,
)

embeddings = GigaChatEmbeddings(
    credentials=AUTH_KEY,
    verify_ssl_certs=False,
    scope="GIGACHAT_API_PERS"
)