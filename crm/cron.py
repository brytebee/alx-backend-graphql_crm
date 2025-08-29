import datetime, requests
# from gql.transport.requests import RequestsHTTPTransport
# from gql import gql, Client

def log_crm_heartbeat():
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    with open("/tmp/crm_heartbeat_log.txt", "a") as f:
        f.write(f"{timestamp} CRM is alive\n")

def update_low_stock():
    endpoint = "http://localhost:8000/graphql"
    mutation = """
    mutation {
      updateLowStockProducts {
        updatedProducts { name stock }
        message
      }
    }
    """
    response = requests.post(endpoint, json={"query": mutation})
    data = response.json().get("data", {}).get("updateLowStockProducts", {})

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("/tmp/low_stock_updates_log.txt", "a") as f:
        for p in data.get("updatedProducts", []):
            f.write(f"{timestamp} - {p['name']} restocked to {p['stock']}\n")
