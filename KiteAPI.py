from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import requests
import hashlib
import json
import csv
import os


api_key = "your_api_key"
api_secret = "your_api_secret"



filename = "access_token.json"

# Check if access token exists
if os.path.exists(filename):
    with open(filename, "r") as json_file:
        token_data = json.load(json_file)
        access_token = token_data["access_token"]
        username = token_data["username"]
    print(f"Using existing Access Token for user: {username}")
else:
    login_url = f"https://kite.zerodha.com/connect/login?v=3&api_key={api_key}"
    driver = webdriver.Chrome()
    driver.get(login_url)


    while "request_token=" not in driver.current_url:
        time.sleep(2)  #Checks for login after every 2 seconds
    
    current_url = driver.current_url
    request_token_start = current_url.find("request_token=") + len("request_token=")
    request_token_end = current_url.find("&", request_token_start)
    request_token = current_url[request_token_start:request_token_end]

    
    if not request_token:
        print("Login failed. Unable to obtain request token.")
    else:
        print(f"Request Token: {request_token}")


        driver.quit()


        token_url = "https://api.kite.trade/session/token"

        checksum_data = f"{api_key}{request_token}{api_secret}".encode('utf-8')
        checksum = hashlib.sha256(checksum_data).hexdigest()

        token_data = {
            "api_key": api_key,
            "request_token": request_token,
            "checksum": checksum
        }

        headers = {
            "X-Kite-Version": "3"
        }

        response = requests.post(token_url, data=token_data, headers=headers)
        token_response = response.json()
        access_token=""
        # Extract access token and username from the response
        if token_response["status"]!="error":
            access_token = token_response["data"]["access_token"]
            username = token_response["data"]["user_name"]

            # Save access token and username as JSON in a file
            with open(filename, "w") as json_file:
                json.dump({"username": username, "access_token": access_token}, json_file, indent=2)

            print(f"Access Token and Username saved to {filename}")
        else:
            print("Unable to get request_token")


if not access_token:
    print("Login failed. Unable to obtain request token.")
else:
    # Fetch user's holdings using the access token
    holdings_url = "https://api.kite.trade/portfolio/holdings"

    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {api_key}:{access_token}"
    }

    holdings_response = requests.get(holdings_url, headers=headers).json()

   
    holdings_data = holdings_response["data"]
    holdings_list = []

    for holding in holdings_data:
        Stock_Name = holding["tradingsymbol"]
        quantity = holding["quantity"]
        last_price = holding["last_price"]
        average_price = holding["average_price"]
        close_price = holding["close_price"]

        holding_entry = {
            "Stock Name": Stock_Name,
            "Quantity": quantity,
            "Average Price": average_price,
            "Last Price": last_price,
            "Close Price": close_price
        }

        holdings_list.append(holding_entry)
    
    csv_filename = f"{username}_holdings.csv"
    csv_fields = ["Stock Name", "Quantity", "Average Price", "Last Price", "Close Price"]

    with open(csv_filename, mode='w', newline='') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
        csv_writer.writeheader()
        csv_writer.writerows(holdings_list)
    print(f"Holdings saved to {csv_filename}")
