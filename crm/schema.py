# crm/schema.py
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .mutations import CreateCustomer, BulkCreateCustomers, CreateProduct, CreateOrder
from .types import CustomerType, ProductType, OrderType
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter

class Query(graphene.ObjectType):
    # Simple hello field
    hello = graphene.String(default_value="Hello World!")
    
    # Basic queries without filters
    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)
    
    # Individual item queries
    customer = graphene.Field(CustomerType, id=graphene.ID())
    product = graphene.Field(ProductType, id=graphene.ID())
    order = graphene.Field(OrderType, id=graphene.ID())
    
    # Filtered queries with Django Filter Connection Fields
    filtered_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter)
    filtered_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter)
    filtered_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter)

    def resolve_all_customers(self, info):
        return Customer.objects.all()

    def resolve_all_products(self, info):
        return Product.objects.all()

    def resolve_all_orders(self, info):
        return Order.objects.all()

    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None

    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None

    def resolve_order(self, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
