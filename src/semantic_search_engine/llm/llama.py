'''
    You can run this to install LLaMA2 7B on your local machine.
'''

from huggingface_hub import login
# Use a pipeline for later
from transformers import pipeline

import torch
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM

login()


tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf",
                                          use_auth_token=True,)

model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat-hf",
                                             device_map='auto',
                                             torch_dtype=torch.float16,
                                             use_auth_token=True,
                                            #  load_in_8bit=True,
                                             load_in_4bit=True
                                             )




pipe = pipeline("text-generation",
                model=model,
                tokenizer= tokenizer,
                torch_dtype=torch.float16,
                device_map="auto",
                do_sample=True,
                top_k=30,
                num_return_sequences=1,
                eos_token_id=tokenizer.eos_token_id
                )