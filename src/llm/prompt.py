import textwrap
from langchain import PromptTemplate
from langchain.memory import ConversationBufferMemory

class Prompt:
    
    def __init__(self, system_prompt, instruction):
        self.system_prompt = system_prompt
        self.instruction = instruction
    
    def get_prompt_template(self):

        B_INST, E_INST = "[INST]", "[/INST]"
        B_SYS, E_SYS = "\n<<SYS>>\n", "\n<</SYS>>\n\n"
        SYSTEM_PROMPT = B_SYS + self.system_prompt + E_SYS
        
        prompt_template =  B_INST + SYSTEM_PROMPT + self.instruction + E_INST
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
        return (wrapped_text +'\n\n')


    def get_prompt(self):

        template = self.get_prompt_template()
        # print(template)

        prompt = PromptTemplate(
            input_variables=["context", "chat_history", "user_input"], template=template
        )

        return prompt
    
    # This is the history of every prompt given to the chain (Can be used as chat history)
    def get_buffer_memory(self):
        memory = ConversationBufferMemory(memory_key="chat_history", input_key="user_input")
        return memory