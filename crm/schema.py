# crm/schema.py
import graphene
from .mutations import CreateCustomer


class Query(graphene.ObjectType):
    # Simple hello field
    hello = graphene.String(default_value="Hello World!")


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer

schema = graphene.Schema(query=Query)
