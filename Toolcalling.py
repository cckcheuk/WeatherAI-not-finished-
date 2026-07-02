from flask import Flask, request
import json
import requests

app = Flask(__name__)


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_hk_weather",
            "description": "Get the current weather in Hong Kong from the HKO.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

#Get the current weather in Hong Kong from the HKO API
def get_hko_api():
    hko_api = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=tc"
    
#try to get the current weather data from the HKO API
    try:
        response = requests.get(hko_api, timeout=10)
        data = response.json()

#here I only try the temperature data, it can also add humidity, wind speed, etc.
        temperature = None

#Find the temperature data for Hong Kong Observatory
        for item in data['temperature']['data']:
            if item['place'] == 'Hong Kong Observatory':
                temperature = f"{item['value']}°C"
                break
        
        return {
            "temperature": temperature,
        }

    except Exception as e:
        return {"fail to load data": str(e)}
    
#pack the prompt message and question to send to the AI model, and handle the response
def ai_response(question):
    messages = [
        #system prompt and user prompt
        {"role": "system", "content": "You are the weather assistant, use that tool to call and answer user's question."},
        {"role": "user", "content": question}
    ]

    load = {
        "model": "google/gemma-4-e4b",
        "messages": messages,
        "tools": tools
    }

    try:
        response = requests.post(
            "http://localhost:1234/api/v1/chat",
            json=load)
        # check the status code
        if response.status_code != 200:
            return f"Error from AI: {response.status_code} "
        
        data = response.json()
        ai_message = data['choices'][0]['message']

    # check if the AI message need a function call, 
        if ai_message.get('function_call'):
            #tool calling
            for tool_call in ai_message['tool_calls']:
                function_name = tool_call['function']['name']
                if function_name == "get_hk_weather":
                    api_result = get_hko_api()

                    # put the tool call result back to messages
                    messages.append(ai_message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call['id'],
                        "name": function_name,
                        "content": json.dumps(api_result) #transfer to json format
                    })
            
            #let ai based on tool result to answer the question
            final_load = {
                "model": "google/gemma-4-e4b",
                "messages": messages
            }
            final_response = requests.post("http://localhost:1234/api/v1/chat", json=final_load)
            final_data = final_response.json()
            return final_data['choices'][0]['message']['content']
        
        #if the ai wasnt calling the tool, just return the answer
        else:
            return ai_message['content']
