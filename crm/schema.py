# crm/schema.py
import graphene

class Query(graphene.ObjectType):
    # Simple hello field
    hello = graphene.String(default_value="Hello World!")

schema = graphene.Schema(query=Query)
