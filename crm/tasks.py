import datetime, requests
# from datetime import datetime
# import requests
from celery import shared_task

@shared_task
def generate_crm_report():
    endpoint = "http://localhost:8000/graphql"
    query = """
    query {
      allCustomers { id }
      allOrders { id totalAmount }
    }
    """
    response = requests.post(endpoint, json={"query": query})
    data = response.json().get("data", {})

    customers = data.get("allCustomers", [])
    orders = data.get("allOrders", [])
    total_customers = len(customers)
    total_orders = len(orders)
    total_revenue = sum([float(o["totalAmount"]) for o in orders if o.get("totalAmount")])

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("/tmp/crm_report_log.txt", "a") as f:
        f.write(f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, {total_revenue} revenue\n")
