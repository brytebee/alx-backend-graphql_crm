# crm/schema.py
import graphene
import datetime
from django.utils import timezone
from graphene_django.filter import DjangoFilterConnectionField
from .mutations import CreateCustomer, BulkCreateCustomers, CreateProduct, CreateOrder, UpdateLowStockProducts
from .types import CustomerType, ProductType, OrderType
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter

# Custom input types for filtering
class CustomerFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    email_icontains = graphene.String()
    created_at_gte = graphene.DateTime()
    created_at_lte = graphene.DateTime()
    phone_pattern = graphene.String()

class ProductFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    price_gte = graphene.Decimal()
    price_lte = graphene.Decimal()
    stock_gte = graphene.Int()
    stock_lte = graphene.Int()
    low_stock = graphene.Boolean()

class OrderFilterInput(graphene.InputObjectType):
    total_amount_gte = graphene.Decimal()
    total_amount_lte = graphene.Decimal()
    order_date_gte = graphene.DateTime()
    order_date_lte = graphene.DateTime()
    customer_name = graphene.String()
    product_name = graphene.String()
    product_id = graphene.ID()

# Connection classes for relay-style pagination
class CustomerConnection(graphene.relay.Connection):
    class Meta:
        node = CustomerType

class ProductConnection(graphene.relay.Connection):
    class Meta:
        node = ProductType

class OrderConnection(graphene.relay.Connection):
    class Meta:
        node = OrderType

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
    
    # Custom filtered queries with ordering support
    customers_filtered = graphene.List(
        CustomerType,
        filter=CustomerFilterInput(),
        order_by=graphene.String(default_value="id")
    )
    
    products_filtered = graphene.List(
        ProductType,
        filter=ProductFilterInput(),
        order_by=graphene.String(default_value="id")
    )
    
    orders_filtered = graphene.List(
        OrderType,
        filter=OrderFilterInput(),
        order_by=graphene.String(default_value="id")
    )

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

    def resolve_customers_filtered(self, info, filter=None, order_by="id"):
        queryset = Customer.objects.all()
        
        if filter:
            if filter.get('name_icontains'):
                queryset = queryset.filter(name__icontains=filter['name_icontains'])
            if filter.get('email_icontains'):
                queryset = queryset.filter(email__icontains=filter['email_icontains'])
            if filter.get('created_at_gte'):
                queryset = queryset.filter(created_at__gte=filter['created_at_gte'])
            if filter.get('created_at_lte'):
                queryset = queryset.filter(created_at__lte=filter['created_at_lte'])
            if filter.get('phone_pattern'):
                queryset = queryset.filter(phone__startswith=filter['phone_pattern'])
        
        return queryset.order_by(order_by)

    def resolve_products_filtered(self, info, filter=None, order_by="id"):
        queryset = Product.objects.all()
        
        if filter:
            if filter.get('name_icontains'):
                queryset = queryset.filter(name__icontains=filter['name_icontains'])
            if filter.get('price_gte'):
                queryset = queryset.filter(price__gte=filter['price_gte'])
            if filter.get('price_lte'):
                queryset = queryset.filter(price__lte=filter['price_lte'])
            if filter.get('stock_gte'):
                queryset = queryset.filter(stock__gte=filter['stock_gte'])
            if filter.get('stock_lte'):
                queryset = queryset.filter(stock__lte=filter['stock_lte'])
            if filter.get('low_stock'):
                queryset = queryset.filter(stock__lt=10)
        
        return queryset.order_by(order_by)

    def resolve_orders_filtered(self, info, filter=None, order_by="id"):
        queryset = Order.objects.all()
        
        if filter:
            if filter.get('total_amount_gte'):
                queryset = queryset.filter(total_amount__gte=filter['total_amount_gte'])
            if filter.get('total_amount_lte'):
                queryset = queryset.filter(total_amount__lte=filter['total_amount_lte'])
            if filter.get('order_date_gte'):
                queryset = queryset.filter(order_date__gte=filter['order_date_gte'])
            if filter.get('order_date_lte'):
                queryset = queryset.filter(order_date__lte=filter['order_date_lte'])
            if filter.get('customer_name'):
                queryset = queryset.filter(customer__name__icontains=filter['customer_name'])
            if filter.get('product_name'):
                queryset = queryset.filter(products__name__icontains=filter['product_name'])
            if filter.get('product_id'):
                queryset = queryset.filter(products__id=filter['product_id'])
        
        return queryset.distinct().order_by(order_by)
    
    orders_last7days = graphene.List(OrderType)
    def resolve_orders_last7days(self, info):
        cutoff = timezone.now() - datetime.timedelta(days=7)
        return Order.objects.filter(order_date__gte=cutoff)


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
