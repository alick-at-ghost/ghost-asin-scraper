from openai import OpenAI
import pandas as pd
from credentials import credentials


def call_openai(prompt, system_message="You are a world class AI assitant."):
    print(f"Running OpenAI request")
    client = OpenAI(api_key=credentials["opeanai_api_key"])

    message = []

    message.append(
        {"role": "system", "content": f"{system_message}"})
    message.append({"role": "user", "content": f"{prompt}"})

    response = client.chat.completions.create(model="gpt-4-turbo-preview",
                                              messages=message,
                                              # max_tokens=1500,
                                              temperature=0,
                                              stream=False)
    return response.choices[0].message.content.strip().strip('\'"')