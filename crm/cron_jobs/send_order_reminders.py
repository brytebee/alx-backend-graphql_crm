#!/usr/bin/env python3
import datetime, requests
# from gql import gql, Client 

endpoint = "http://localhost:8000/graphql"

# Query the new orders_last7days field
query = """
query {
  ordersLast7days {
    id
    customer {
      email
    }
  }
}
"""

response = requests.post(endpoint, json={"query": query})
data = response.json().get("data", {}).get("ordersLast7days", [])

timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open("/tmp/order_reminders_log.txt", "a") as f:
    for order in data:
        f.write(f"{timestamp} - Order {order['id']} reminder for {order['customer']['email']}\n")

print("Order reminders processed!")
