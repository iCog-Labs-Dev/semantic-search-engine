import together

# import logging
from typing import Any, Dict #, List, Mapping, Optional

from pydantic import Extra, root_validator #, Field

# from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
# from langchain.llms.utils import enforce_stop_tokens
from langchain.utils import get_from_dict_or_env

class TogetherLLM(LLM):
    """Together large language models."""

    model: str = "togethercomputer/llama-2-70b-chat"
    """model endpoint to use"""

    together_api_key: str = '-------------------'
    """Together API key"""

    temperature: float = 0.7
    """What sampling temperature to use."""

    max_tokens: int = 512
    """The maximum number of tokens to generate in the completion."""

    # def __init__(self):
    #     # create an inner class object
    #     self.config = self.Config()

    class Config:
        extra = Extra.forbid
    
    def start_model(self):
        # Start the llama2 70B model
        try:
            together.api_key = self.together_api_key
            together.Models.start(self.model)
        except:
            return 'Failed to start model!'
        return 'Model started!'
    
    def stop_model(self):
        # Stop the llama2 70B model
        try:
            together.api_key = self.together_api_key
            together.Models.stop(self.model)
        except:
            return 'Failed to stop model!'
        return 'Model stopped!'

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that the API key is set."""
        api_key = get_from_dict_or_env(
            values, "together_api_key", "TOGETHER_API_KEY"
        )
        values["together_api_key"] = api_key
        return values

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
        try:
            output = together.Complete.create(prompt,
                                            model=self.model,
                                            max_tokens=self.max_tokens,
                                            temperature=self.temperature,
                                            )
            text = output['output']['choices'][0]['text']
        except together.error.InstanceError:
            return f'The model "{ self.model }" is not running on together.ai'
        except:
            return 'An error occurred!'
        
        return text

