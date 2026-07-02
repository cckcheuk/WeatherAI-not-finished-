from flask import Flask
import os
import requests
import json

app = Flask(__name__)
HKO_API = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=flw&lang=en"

def get_weather():
    try:
        resp = requests.get(HKO_API, timeout=10)
        data = resp.json()
        info = "[Weather Information]\n"
    
        for item in data['temperature']['data']:
            if item['place'] == 'Hong Kong Observatory':
                info += f"Temperature: {item['value']}°C\n"
                break
    #tbc, just test tem first

        return info

    except Exception as e:
        return f"Error fetching weather data: {str(e)}"

def ask_ai(question, weather_info):
    system_prompt = f"You are the weather assistant, use that data you get to answer user's question.{weather_info}"

    prompt = {
        "model": "google/gemma-4-e4b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
    }

    response = requests.post(
    "http://localhost:1234/api/v1/chat",
    headers={
        "Content-Type": "application/json"
    },
    json=prompt
    )
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error from AI: {response.status_code} - {response.text}"
