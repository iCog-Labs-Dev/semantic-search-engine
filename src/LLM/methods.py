import json
import textwrap
from ..database.chroma import *
from ..util.format_prompt import *
from llama import *
'''
  You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful,
  unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

  If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question,
  please don't share false information. Don't provide any information you weren't asked to provide.
'''

B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
DEFAULT_SYSTEM_PROMPT = """\
  You will be given a sequence of chat messages related to a certain topic. Write a response that answers the question based on what is discussed in the chat messages.
  Do not mention anything outside of what is discussed. Don't answer anything outside the context you are provided.
  If there isn't enough context, simply reply "This topic was not discussed previously"
  """

SYSTEM_PROMPT = B_SYS + DEFAULT_SYSTEM_PROMPT + E_SYS

def get_prompt(instruction):
    prompt_template =  B_INST + SYSTEM_PROMPT + instruction + E_INST
    return prompt_template

## Helper function to format the response
def cut_off_text(text, prompt):
    cutoff_phrase = prompt
    index = text.find(cutoff_phrase)
    if index != -1:
        return text[:index]
    else:
        return text

def remove_substring(string, substring):
    return string.replace(substring, "")

def generate(text):
    prompt = get_prompt(text)
    with torch.autocast('cuda', dtype=torch.float16):
        inputs = tokenizer(prompt, return_tensors="pt").to('cuda')
        outputs = model.generate(**inputs,
                                 max_new_tokens=512,
                                 eos_token_id=tokenizer.eos_token_id,
                                 pad_token_id=tokenizer.eos_token_id,
                                 )
        final_outputs = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
        final_outputs = cut_off_text(final_outputs, '</s>')
        final_outputs = remove_substring(final_outputs, prompt)

    return final_outputs#, outputs

def parse_text(text):
        wrapped_text = textwrap.fill(text, width=100)
        return wrapped_text
def semantic_search(query):
  data = get_data_from_chroma(query)

  context = data['context']
  metadata = data['metadata']

  prompt = format_prompt(query, context)
  generated_text = generate(prompt)
  parsed_text = parse_text(generated_text)

  return {'response': parsed_text, 'metadata': metadata}