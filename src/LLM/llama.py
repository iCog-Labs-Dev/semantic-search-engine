import together

import logging
from typing import Any, Dict, List, Mapping, Optional

from pydantic import Extra, Field, root_validator

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from langchain.llms.utils import enforce_stop_tokens
from langchain.utils import get_from_dict_or_env


import json
import textwrap


from langchain import PromptTemplate,  LLMChain
from langchain.memory import ConversationBufferMemory


from ..database.chroma import *
from ..util.format_prompt import *
import os


# set your API key
together_api_key = os.environ["TOGETHER_API_KEY"]
together.api_key = together_api_key

# list available models and descriptons
models = together.Models.list()

# print the first model's name
print(models[3]['name']), print(models[52]['name'])
# List all available models
# for idx, model in enumerate(models):
#     print(idx, model['name'])

# Start the llama2 70B model
together.Models.start("togethercomputer/llama-2-70b-chat")


class TogetherLLM(LLM):
    """Together large language models."""

    model: str = "togethercomputer/llama-2-70b-chat"
    """model endpoint to use"""

    together_api_key: str = os.environ["TOGETHER_API_KEY"]
    """Together API key"""

    temperature: float = 0.7
    """What sampling temperature to use."""

    max_tokens: int = 512
    """The maximum number of tokens to generate in the completion."""

    class Config:
        extra = Extra.forbid

    # @root_validator()
    # def validate_environment(cls, values: Dict) -> Dict:
    #     """Validate that the API key is set."""
    #     api_key = get_from_dict_or_env(
    #         values, "together_api_key", "TOGETHER_API_KEY"
    #     )
    #     values["together_api_key"] = api_key
    #     return values

    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "together"

    def _call(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> str:
        """Call to Together endpoint."""
        together.api_key = self.together_api_key
        output = together.Complete.create(prompt,
                                          model=self.model,
                                          max_tokens=self.max_tokens,
                                          temperature=self.temperature,
                                          )
        text = output['output']['choices'][0]['text']
        return text

# -----------------------------------------------------------------------------------------


B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "\n<<SYS>>\n", "\n<</SYS>>\n\n"
DEFAULT_SYSTEM_PROMPT = """\
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information."""


def get_prompt(instruction, new_system_prompt=DEFAULT_SYSTEM_PROMPT ):
    SYSTEM_PROMPT = B_SYS + new_system_prompt + E_SYS
    prompt_template =  B_INST + SYSTEM_PROMPT + instruction + E_INST
    return prompt_template

def cut_off_text(text, prompt):
    cutoff_phrase = prompt
    index = text.find(cutoff_phrase)
    if index != -1:
        return text[:index]
    else:
        return text

def remove_substring(string, substring):
    return string.replace(substring, "")


def parse_text(text):
        wrapped_text = textwrap.fill(text, width=100)
        print(wrapped_text +'\n\n')
        # return assistant_text

# ---------------------------------------------------------------------------------------------------

# llm = HuggingFacePipeline(pipeline = pipe, model_kwargs = {'temperature':0})

llm = TogetherLLM(
    model= "togethercomputer/llama-2-70b-chat",
    temperature=0.1,
    max_tokens=512
)


instruction = """
### Chat Messages (Context): \n\n{context} \n\n\n
### Chat History: \n\n{chat_history} \nHuman: {user_input} \nAssistant:\n"""
system_prompt = """
  You are a helpful assistant, you always only answer for the assistant then you stop. You will only answer the question the Human asks.
  You will be given a sequence of chat messages related to a certain topic. Write a response that answers the question based on what is discussed in the chat messages.
  You must answer the question based on only chat messages you are given.
  Don't answer anything outside the context you are provided and do not respond with anything from your general knowledge.
  Try to mention the ones that you get the context from.
  You may also look at the chat history to get additional context if necessary.
  If there isn't enough context, simply reply "This topic was not discussed previously"
  """
  # You may also read the chat history to get additional context

template = get_prompt(instruction, system_prompt)
print(template)

prompt = PromptTemplate(
    input_variables=["context", "chat_history", "user_input"], template=template
)
memory = ConversationBufferMemory(memory_key="chat_history", input_key="user_input")

llm_chain = LLMChain(
    llm=llm,
    prompt=prompt,
    verbose=False,
    memory=memory,
)

# llm_chain.predict(context="Alice: What's an LLM? \n Bob: It's an abbreviation for Large Langage Model.", user_input="Hi, my name is Sam")

# ------------------------------------------------------------------------------------------------

########################################

def semantic_search(query):
  data = get_data_from_chroma(query)

  context = data['context']
  metadata = data['metadata']

  response = llm_chain.predict(context=context, user_input=query)

  return {'response': str(response), 'metadata': metadata}


# semantic_search("Hello, my name is John.")
# semantic_search("What did Tollan say about semantic search?")
# semantic_search("What are some models that are comparable to GPT 3?")
# semantic_search("How can I make some pancakes?")
# semantic_search("What's my name?")
# semantic_search("Alright, Thanks!")