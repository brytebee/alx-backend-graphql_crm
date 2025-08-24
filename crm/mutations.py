# crm/mutations.py
import re
import graphene
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Customer, Product, Order
from .types import CustomerType, ProductType, OrderType

# Input types for mutations
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()

# Output types for mutations
class CustomerResult(graphene.ObjectType):
    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    error = graphene.String()

class BulkCustomerResult(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success_count = graphene.Int()
    error_count = graphene.Int()

# Base class with shared validation and creation logic
class BaseCustomerMutation:
    @classmethod
    def validate_customer_data(cls, name, email, phone=None):
        """Shared validation logic"""
        errors = []
        
        # Validate name
        if not name or not name.strip():
            errors.append("Name is required")

        # Validate email format
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors.append("Invalid email format")
     
        # Validate email uniqueness
        if Customer.objects.filter(email=email).exists():
            errors.append("Email already exists")
        
        # Validate phone format if provided
        if phone and not re.match(r'^(\+[1-9]\d{1,14}|\d{3}-\d{3}-\d{4})$', phone):
            errors.append("Invalid phone format")
            
        return errors

    @classmethod
    def create_customer_safe(cls, name, email, phone=None):
        """Safe customer creation with validation - returns (customer, errors)"""
        errors = cls.validate_customer_data(name, email, phone)
        
        if errors:
            return None, errors
        
        try:
            customer = Customer.objects.create(
                name=name.strip(),
                email=email.lower().strip(), 
                phone=phone
            )
            return customer, None
        except Exception as e:
            return None, [f"Database error: {str(e)}"]

class CreateCustomer(BaseCustomerMutation, graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, input):
        customer, errors = CreateCustomer.create_customer_safe(
            input.name, input.email, input.phone
        )
        
        if errors:
            raise Exception("; ".join(errors))
        
        return CreateCustomer(
            customer=customer, 
            message="Customer created successfully.", 
            success=True
        )

class BulkCreateCustomers(BaseCustomerMutation, graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success_count = graphene.Int()
    error_count = graphene.Int()

    def mutate(self, info, input):
        if not input:
            raise Exception("No customers provided")
        
        customers = []
        errors = []
        
        # Process each customer
        for i, customer_data in enumerate(input):
            try:
                customer, validation_errors = BulkCreateCustomers.create_customer_safe(
                    customer_data.name,
                    customer_data.email, 
                    customer_data.phone
                )
                
                if customer:
                    customers.append(customer)
                else:
                    errors.extend([f"Customer {i+1}: {error}" for error in validation_errors])
                    
            except Exception as e:
                errors.append(f"Customer {i+1}: {str(e)}")
        
        return BulkCreateCustomers(
            customers=customers,
            errors=errors,
            success_count=len(customers),
            error_count=len(errors)
        )

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, input):
        errors = []
        
        # Validate price - should be positive
        if input.price is None or input.price <= 0:
            errors.append("Price must be greater than 0")
        
        # Validate stock - should be non-negative (0 is allowed per requirements)
        stock = input.stock if input.stock is not None else 0
        if stock < 0:
            errors.append("Stock must be non-negative")

        if errors:
            raise Exception("; ".join(errors))
        
        try:
            product = Product.objects.create(
                name=input.name, 
                price=input.price, 
                stock=stock
            )
            return CreateProduct(
                product=product, 
                message="Product created successfully.",
                success=True
            )

        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, input):
        errors = []
        
        # Validate customer_id
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            errors.append(f"Customer with ID {input.customer_id} does not exist")
            customer = None
        
        # Validate product_ids
        if not input.product_ids:
            errors.append("At least one product ID is required")
        else:
            # Check if all products exist
            products = Product.objects.filter(id__in=input.product_ids)
            existing_product_ids = set(str(p.id) for p in products)
            provided_product_ids = set(str(pid) for pid in input.product_ids)
            
            missing_ids = provided_product_ids - existing_product_ids
            if missing_ids:
                errors.append(f"Invalid product ID: {', '.join(missing_ids)}")
        
        if errors:
            raise Exception("; ".join(errors))
        
        # Set order_date to now if not provided
        order_date = input.order_date if input.order_date else timezone.now()
        
        try:
            with transaction.atomic():
                # Calculate total amount
                total_amount = sum(product.price for product in products)
                
                # Create the order
                order = Order.objects.create(
                    customer=customer,
                    total_amount=total_amount,
                    order_date=order_date
                )
                
                # Associate products with the order
                order.products.set(products)
                
                return CreateOrder(
                    order=order,
                    message="Order created successfully.",
                    success=True
                )
        
        except Exception as e:
            raise Exception(f"Failed to create order: {str(e)}")
