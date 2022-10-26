import json
import requests

class telegram():
    bot_name = "BTvsActual"
    Token = open("Telegram_token.cred").read()
    base_url = f"https://api.telegram.org/bot{Token}"

    class group():
        BT_Vs_Actual_diff = "-1001755441702"
        Weekly_trade = "-600877495"

    def getUpdates(self):
        url = f"{self.base_url}/getUpdates"
        return requests.post(url)

    def send_message(self, group, message):
        """ Send message """
        url = f"{self.base_url}/sendMessage"
        parameters = { "chat_id":group, "text":message, "parse_mode":"Markdown" }
        try:
            response = requests.post(url, params=parameters)
            return response
        except Exception as e:
            print(str(e) + '\n' + message)
            

    def send_image(self, group, image_path, caption):
        """  Send Image from file path  """
        url = f"{self.base_url}/sendPhoto" 
        parameters = { "chat_id":group, "caption":caption, "parse_mode":"Markdown" }
        files = { "photo" : open(image_path,'rb') }
        try:
            response = requests.post(url, params=parameters, files=files)
            return response
        except Exception as e:
            print(e)

    def send_documents(self, group, file_path, caption):
        """ Send Documents """
        url = f"{self.base_url}/sendDocument"
        parameters = { "chat_id": group, "caption": caption, "parse_mode":"Markdown" }
        files = { "document": open(file_path, 'rb') }
        try:
            response = requests.post(url, params=parameters, files=files)
            return response
        except Exception as e:
            print(e)
            
    def send_poll(self, group, question, option_list):
        """" Send Poll Message """
        url = f"{self.base_url}/sendPoll"
        parameters = { "chat_id":group, "question":question,  "options":json.dumps(option_list), "is_anonymous":False, "type":"quiz", "correct_option_id":0}
        try:
            response = requests.post(url, params=parameters)
            return response
        except Exception as e:
            print(e)
        