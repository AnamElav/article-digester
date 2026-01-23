from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
response = llm.invoke("Say hello")
print(response.content)
