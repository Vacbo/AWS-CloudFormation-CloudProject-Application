from locust import FastHttpUser, task, between
import random
import uuid
from pyquery import PyQuery
import logging

class FastAPIUser(FastHttpUser):
    host = "http://bolaoportella.com" # Change this to the URL to the one aws provides you
    wait_time = between(5, 10)

    @task(5)
    def read_bets(self):
        # Read the main page (contains the list of bets)
        response = self.client.get("/")
        if response.status_code != 200:
            logging.error(f"Failed to read bets: {response.status_code}")
        else:
            logging.info("Successfully read bets")

    @task(4)
    def add_bet(self):
        # If the user alread has a bet it will update it
        predicted_time = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"
        response = self.client.post("/add_bet", data={"name": self.known_bet_name, "predicted_time": predicted_time})
        if response.status_code != 200:
            logging.error(f"Failed to add bet: {response.status_code}")
        else:
            logging.info(f"Successfully added bet: {self.known_bet_name}")

    @task(1)
    def delete_bet(self):
        response = self.client.get("/")
        if response.status_code == 200:
            document = PyQuery(response.content)
            bet_items = document("li")
            for item in bet_items.items():
                name = item.find("span").eq(0).text()
                if name == self.known_bet_name:
                    delete_response = self.client.get(f"/{self.known_bet_name}")
                    if delete_response.status_code == 200:
                        logging.info(f"Successfully deleted bet: {self.known_bet_name}")
                    else:
                        logging.error(f"Failed to delete bet: {delete_response.status_code}")
                    break
        else:
            logging.error(f"Failed to load bets for deletion: {response.status_code}")

    def on_start(self):
        # Create a unique name for the bet, so 2 uses don't collide
        self.known_bet_name = str(uuid.uuid4())

    def on_stop(self):
        # Delete all bets when the Locust process stops
        while True:
            response = self.client.get("/")
            if response.status_code == 200:
                document = PyQuery(response.content)
                bet_items = document("li")
                if not bet_items:
                    break
                for item in bet_items.items():
                    name = item.find("span").eq(0).text()
                    delete_response = self.client.get(f"/{name}")
                    if delete_response.status_code == 200:
                        logging.info(f"Successfully deleted bet: {name}")
                    else:
                        logging.error(f"Failed to delete bet: {delete_response.status_code}")
            else:
                logging.error(f"Failed to load bets for deletion: {response.status_code}")
                break