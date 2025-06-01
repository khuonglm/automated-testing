import os
import time
import google.generativeai as genai
from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

_MAX_RETRIES = int(os.getenv("MODEL_MAX_RETRIES", 3))

class ModelArguments:
    """Arguments configuring the model and its behavior."""
    # Name of the model to use
    model_name: str
    # Sampling temperature
    temperature: float = 0.1
    # Sampling top-p
    top_p: float = 0.85

    def __init__(self, model_name: str, temperature: float = 0.1, top_p: float = 0.85):
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p

class BaseModel:
    MODELS = {}
    def __init__(self, args: ModelArguments):
        self.args = args

    def query(self, history: list[dict[str, str]]) -> str:
        msg = "Use a subclass of BaseModel"
        raise NotImplementedError(msg)

class GoogleModel(BaseModel):
    # Check https://ai.google.dev/gemini-api/docs/models/gemini for model names, context
    # Check https://ai.google.dev/pricing#1_5flash for pricing, rate limits
    # Available models:
    MODELS = {
        "models/gemini-2.0-flash-lite": {
            "max_context": 1_048_576,
        },
        "models/gemini-2.0-flash": {
            "max_context": 1_048_576,
        },
        "models/gemini-1.5-flash": {
            "max_context": 1_048_576,
        },
        "models/gemini-1.5-flash-8b": {
            "max_context": 1_048_576,
        },
        "models/gemini-1.5-pro": {
            "max_context": 2_097_152,
        },
        "models/text-embedding-004": {
            "max_context": 2048,
        },
    }

    def __init__(self, args: ModelArguments):
        super().__init__(args)
        # Set Google key
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    @retry(
        wait=wait_random_exponential(min=1, max=15),
        stop=stop_after_attempt(_MAX_RETRIES),
    )
    def query(self, system_instruction: str, user_messages: str) -> str:
        """
        Query the Google API
        """
        try:
            time.sleep(1)
            model = genai.GenerativeModel(
                model_name=self.args.model_name,
                generation_config=genai.GenerationConfig(
                    temperature=self.args.temperature,
                    top_p=self.args.top_p,
                ),
                system_instruction=system_instruction,
            )
            response = model.generate_content(user_messages)
        except Exception as e:
            return None
        return response.text