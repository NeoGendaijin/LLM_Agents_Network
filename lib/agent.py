import re
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
from typing import Any, Dict, List, Optional
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from faker import Faker
from lib.memory import Memory
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import random
import tiktoken
import os

load_dotenv()

class Agent:
    """Generative Agent"""

    def __init__(self, id: str, bias: str = "none", model: str = "gpt-3.5-turbo") -> None:

        if "mistral" in model:
            llm = Ollama(model="mistral")
        elif model == "phi":
            llm = Ollama(model="phi")
        elif "gpt-3.5-turbo" in model:
            llm = ChatOpenAI(
                max_tokens=200,
                temperature=0.7,
                request_timeout=60,
                max_retries=5
            )
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")  # Tokenizer for GPT-3.5
        elif "gpt-4o-mini" in model:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=2000,
                request_timeout=60,
                max_retries=5
            )
            self.tokenizer = tiktoken.encoding_for_model("gpt-4o-mini")  # Tokenizer for GPT-4o-mini
        else:
            raise ValueError(f"Unknown model: {model}")

        self.id = id
        self.name = fake_name()
        self.verbose = False
        self.response = ""
        self.neighbor_response = ""
        self.llm = llm
        self.memory = Memory(model=model)
        self.bias = bias

    @staticmethod
    def _parse_list(text: str) -> List[str]:
        """Parse a newline-separated string into a list of strings."""
        lines = re.split(r"\n", text.strip())
        return [re.sub(r"^\s*\d+\.\s*", "", line).strip() for line in lines]

    def chain(self, prompt: PromptTemplate) -> LLMChain:
        return LLMChain(llm=self.llm, prompt=prompt, verbose=self.verbose)

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text."""
        return len(self.tokenizer.encode(text))

    def interview(self, question: str, correspodee: str = "Interviewer") -> str:
        """Generate a response to a given prompt."""
        prompt = PromptTemplate.from_template(
            "{correspondee}: {question}"
            +"\n{agent_name}:"
        )

        kwargs: Dict[str, Any] = dict(
            agent_name=self.name,
            question=question,
            correspondee=correspodee,
        )

        response = self.chain(prompt=prompt).invoke(kwargs)["text"].strip()

        return response

    @retry(wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type(Exception),  # Customize based on the exceptions you expect
        reraise=True)
    async def ainterview(self, question: str, correspondee: str = "Interviewer") -> str:
        """Generate a response to a given prompt."""
        prompt = PromptTemplate.from_template(
            "{correspondee}: {question}"
            + "\n{agent_name}:"
        )

        kwargs: Dict[str, Any] = dict(
            agent_name=self.name,
            question=question,
            correspondee=correspondee,
        )

        response = await self.chain(prompt=prompt).ainvoke(kwargs)
        input_tokens = self.count_tokens(prompt.format(**kwargs))
        return response["text"].strip(), input_tokens

def fake_hobby():
    hobbies = ["Reading", "Hiking", "Painting", "Cooking", "Gaming", "Traveling", "Photography", "Gardening", "Yoga", "Dancing"]
    return random.choice(hobbies)

def fake_name():
    fake = Faker()
    return fake.name()

def fake_job():
    fake = Faker()
    return fake.job()

def fake_age():
    return random.randint(18, 65)

def solve_math_problems(input_str):
    pattern = r"\d+\.?\d*"

    matches = re.findall(pattern, input_str)
    if matches:
        return matches[-1]

    return None

def parse_response_mmlu(response: str) -> Optional[str]:
    """
    Parse the response for MMLU questions
    """

    pattern = r'\(([a-zA-Z])\)'
    matches = re.findall(pattern, response)

    answer = None

    for match_str in matches[::-1]:
        answer = match_str.upper()
        if answer:
            break

    return answer

def fake_name():
    fake = Faker()
    return fake.name()
