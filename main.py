from unittest import result
from django.http import response
import requests
import json 
import pyttsx3
import speech_recognition as sr
import re
import threading
import time



API_KEY = "tj1Dn0TnADie"
PROJECT_TOKEN = "tfD836TrUdJM"
RUN_TOKEN = "tacbXtqYYq97"

# HTTP REQUEST: GET https://parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data
# GET DATA FOR A RUN: GET https://parsehub.com/api/v2/runs/{RUN_TOKEN}/data
# CANCEL A RUN: POST https://parsehub.com/api/v2/runs/{RUN_TOKEN}/cancel
# DELETE A RUN: DELETE https://parsehub.com/api/v2/runs/{RUN_TOKEN}


class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key  
        self.project_token = project_token
        self.params = {
            "api_key": self.api_key
        }
        self.data = self.get_data()
    
    def get_data(self):
        response = requests.get(
            f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data', params={"api_key": API_KEY}
        )
        data = json.loads(response.text)
        return data

    def get_total_cases(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Coronavirus Cases:":
                return content['value']
        return "0"
    
    def get_total_deaths(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Deaths:":
                return content['value']
        return "0"

    def get_total_recovered(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Recovered:":
                return content['value']
        return "0"
    
    def get_country_data(self, country):
        data = self.data['country']

        for content in data:
            if content['name'].lower() == country.lower():
                return content
        return "0"

    def get_list_of_countries(self):
        countries = []
        for country in self.data['country']:
            countries.append(country['name'].lower())
        return countries

    # update
    def update_data(self):
        response = requests.post(
            f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/run', params={"api_key": API_KEY}
        )

        def poll():
            time.sleep(0.1)
            old_data = self.data
            while True:
                new_data = self.get_data()
                if new_data != old_data:
                    self.data = new_data
                    print("Data has been updated!")
                    break
                time.sleep(5)

        t = threading.Thread(target=poll)
        t.start()
        

# COMPUTER SPEAK TO US:
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio)
        except Exception as e:
            print("Exception:", str(e))

    return said.lower()

def main():
    listening = True
    data = Data(API_KEY, PROJECT_TOKEN)
    print("Started Program")
    END_PHRASE = "stop"
    country_list = data.get_list_of_countries()

    TOTAL_PATTERNS = {
                    re.compile("[\w\s] + total + [\w\s] + cases"):data.get_total_cases,
                    re.compile("[\w\s] + total cases"):data.get_total_cases,
                    re.compile("[\w\s] + total + [\w\s] + deaths"):data.get_total_deaths,
                    re.compile("[\w\s] + total deaths"):data.get_total_deaths,
                    re.compile("[\w\s] + total + [\w\s] + recovered"):data.get_total_recovered,
                    re.compile("[\w\s] + total recovered"):data.get_total_recovered,
                    }

    COUNTRY_PATTERNS = {
                    re.compile("[\w\s] + cases [\w\s] +"): lambda country: data.get_country_data(country)['total_cases'],
                    re.compile("[\w\s] + deaths [\w\s] +"): lambda country: data.get_country_data(country)['total_deaths'],
                    re.compile("[\w\s] + recovered [\w\s] +"): lambda country: data.get_country_data(country)['total_recovered']
                    }

    UPDATE_COMMAND = "update"

    while listening:
        print("Listening...")
        text = get_audio()
        print(text)
        result = None

        for pattern, func in COUNTRY_PATTERNS.items():
            if pattern.match(text):
                words = set(text.split(" "))
                for country in country_list:
                    if country in words:
                        result = func(country)
                        break
        
        for pattern, func in TOTAL_PATTERNS.items():
            if pattern.match(text):
                result = func()
                break

        
        if text == UPDATE_COMMAND:
            result = "Data is being updated. This may take a moment."
            data.update_data()
        
        if result:
            speak(result)

        if text.find(END_PHRASE) != -1: #this will stop the loop
            print("Exit")
            break

main()









