import os, sys
import enum
import openai

class LanguageModelType(enum.Enum):
    chat_gpt = "chat_gpt"

def load_language_model(**kwargs):
    """
    Load specified LLM model
    
    Parameters:
        model (str): name of model to load
        kwargs (dict): additional config arguments to pass to model
    Returns:
        LanguageModel: instanciated and configured language model sub-class
    """

    # TODO instanciate language model sub-class from given model name

    model_name = kwargs.get('model_name', 'chat_gpt')
    if model_name == 'chat_gpt':
        language_model = ChatGPT(**kwargs)
    else:
        raise ValueError(f"Unknown language model {model_name}")

    return language_model


class LanguageModel():
    """
    Base class for language models
    """

    def __init__(self, **kwargs):

        self.template = self.load_template(kwargs.get("template", "config/templates/default_template.txt"))
        self.similarity_template = self.load_template(kwargs.get("similarity_template", "config/templates/default_similarity_template.txt"))
    
    def check_similarity(self, user_prompt: str, image_caption: str):
        """
        Check similarity between user prompt and image caption
        Determines whether caption is suffiently similar to user prompt to terminate generation process

        Parameters:
            user_prompt (str): user prompt
            image_caption (str): image caption
        Returns:
            bool: True if caption is sufficiently similar to user prompt, False otherwise
        """

        similarity_prompt = self.get_similarity_prompt(user_prompt, image_caption)
        similarity_response = self.query_language_model(similarity_prompt)
        print(similarity_response)

        return 1 if "Yes" in similarity_response else 0


    def generate_optimized_prompt(self, user_prompt: str, image_caption: str, previous_prompts: list = []):
        """
        Generate optimized prompt given original user prompt, image caption, and possibly previous prompts

        Parameters:
            user_prompt (str): user prompt
            image_caption (str): image caption
            previous_prompts (list): list of prompts previously generated by model
        Returns:
            str: optimized prompt
        """

        LLM_prompt = self.get_language_prompt(user_prompt, image_caption, previous_prompts)
        LLM_response = self.query_language_model(LLM_prompt)

        return LLM_response
    
    def load_template(self, template_file: str):
        """
        Load templates from file

        Parameters:
            template_file (str): path to template file
        Returns:
            str: template
        """

        with open(template_file, "r") as f:
            template = f.read()
        
        return template

    def get_language_prompt(self, user_prompt: str, image_caption: str, previous_prompts: list = []):
        """
        Generate language prompt given original user prompt, image caption, and possibly previous prompts

        Parameters:
            user_prompt (str): user prompt
            image_caption (str): image caption
            previous_prompts (list): list of prompts previously generated by model
        Returns:
            str: prompt for language model
        """

        # Replace <USER_PROMPT> in template with user prompt
        prompt = self.template.replace("<USER_PROMPT>", user_prompt)
        # Replace <IMAGE_CAPTION> in template with image caption
        prompt = prompt.replace("<IMAGE_CAPTION>", image_caption)
        # Add optional text for previous prompts
        if len(previous_prompts) > 0:
            #TODO implement properly depending on ultimate syntax for previous prompt definition
            previous_prompt = ""
            for prompt in previous_prompts:
                prompt_prefix = "" #TODO: add prefix for previous prompts
                prompt_suffix = "" #TODO: add suffix for previous prompts
                previous_prompt += prompt_prefix + prompt + prompt_suffix
            prompt = prompt.replace("<PREVIOUS_PROMPTS>", previous_prompt)

        return prompt
    
    def get_similarity_prompt(self, user_prompt: str, image_caption: str):
        """
        Generate similarity prompt given original user prompt and image caption

        Parameters:
            user_prompt (str): user prompt
            image_caption (str): image caption
        Returns:
            str: prompt for similarity check
        """

        # Replace <USER_PROMPT> in template with user prompt
        prompt = self.similarity_template.replace("<USER_PROMPT>", user_prompt)
        # Replace <IMAGE_CAPTION> in template with image caption
        prompt = prompt.replace("<IMAGE_CAPTION>", image_caption)

        return prompt
    
    def query_language_model(self, prompt: str):
        """
        Query language model with prompt
        -> to be implemented by sub-class

        Parameters:
            prompt (str): prompt to query language model with
        Returns:
            str: generated text
        """

        #TODO query language model with prompt -> to be overwritten by sub-class

        raise NotImplementedError
    
    def reset(self):
        """
        Optional method to reset model between generations
        """
        pass


class ChatGPT(LanguageModel):
    """
    Wrapper for OpenAI ChatGPT API
    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.model = LanguageModelType.chat_gpt.value
        self.api_key = kwargs.get("api_key", "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")
        self.token_usage = 0
        self.role = self.load_template(kwargs.get("role", "config/templates/model_role.txt"))
        openai.api_key = self.api_key

    def get_language_prompt(self, user_prompt: str, image_caption: str, previous_prompts: list = []):
        """
        Generate language prompt given original user prompt, image caption, and possibly previous prompts and role of the model

        Parameters:
            user_prompt (str): user prompt
            image_caption (str): image caption
            previous_prompts (list): list of prompts previously generated by model
            role (str): role of model
        Returns:
            str: prompt for language model
        """

        message = [{"role": "system", "content": self.role}]

        # Replace <USER_PROMPT> in template with user prompt
        prompt = self.template.replace("<USER_PROMPT>", user_prompt)
        # Replace <IMAGE_CAPTION> in template with image caption
        prompt = prompt.replace("<IMAGE_CAPTION>", image_caption)

        message.append({"role": "user", "content": prompt})

        return message

    def get_similarity_prompt(self, user_prompt: str, image_caption: str):
        """
        Generate similarity prompt given original user prompt and image caption

        Parameters:
            user_prompt (str): user prompt
            image_caption (str): image caption
        Returns:
            str: prompt for similarity check
        """
        message = [{"role": "system", "content": self.role}]

        # Replace <USER_PROMPT> in template with user prompt
        prompt = self.similarity_template.replace("<USER_PROMPT>", user_prompt)
        # Replace <IMAGE_CAPTION> in template with image caption
        prompt = prompt.replace("<IMAGE_CAPTION>", image_caption)

        message.append({"role": "user", "content": prompt})

        return message

    def query_language_model(self, prompt: str):
        """
        Query language model with prompt

        Parameters:
            prompt (str): prompt to query language model with
        Returns:
            str: generated text
        """
        generated_prompt = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt)

        self.token_usage += generated_prompt['usage']['total_tokens']

        return generated_prompt['choices'][0]['message']['content']

    def reset(self):
        """
        Optional method to reset model between generations
        """
        pass