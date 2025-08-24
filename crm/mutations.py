# crm/mutations.py
import re
import graphene
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Customer, Product, Order
from .types import CustomerType, ProductType, OrderType

# Input type for customer data
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

# Output type for customer data (for results)
class CustomerData(graphene.ObjectType):
    name = graphene.String()
    email = graphene.String()
    phone = graphene.String()

# Result type for individual customer creation
class CustomerResult(graphene.ObjectType):
    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    error = graphene.String()
    input_data = graphene.Field(CustomerData)

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
            errors.append("Invalid phone format. Use +1234567890 or 123-456-7890 format")
            
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
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, name, email, phone=None):
        customer, errors = CreateCustomer.create_customer_safe(name, email, phone)
        
        if errors:
            raise Exception("; ".join(errors))
        
        return CreateCustomer(
            customer=customer, 
            message="Customer created successfully.", 
            success=True
        )

class BulkCreateCustomers(BaseCustomerMutation, graphene.Mutation):
    class Arguments:
        customers = graphene.List(CustomerInput, required=True)
        fail_on_error = graphene.Boolean(default_value=False)

    results = graphene.List(CustomerResult)
    total_count = graphene.Int()
    success_count = graphene.Int()
    error_count = graphene.Int()
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, customers, fail_on_error=False):
        if not customers:
            raise Exception("No customers provided")
        
        results = []
        successful_customers = []
        has_errors = False
        
        # Pre-validate all customers if fail_on_error is True
        if fail_on_error:
            validation_errors = []
            for i, customer_data in enumerate(customers):
                errors = BulkCreateCustomers.validate_customer_data(
                    customer_data.name,
                    customer_data.email, 
                    customer_data.phone
                )
                if errors:
                    validation_errors.extend([f"Customer {i+1}: {error}" for error in errors])
            
            if validation_errors:
                raise Exception("Validation failed: " + "; ".join(validation_errors))
        
        # Process each customer with atomic transactions for consistency
        with transaction.atomic():
            for i, customer_data in enumerate(customers):
                input_data = CustomerData(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.phone
                )
                
                # Create savepoint for individual customer
                sid = transaction.savepoint()
                
                try:
                    customer, errors = BulkCreateCustomers.create_customer_safe(
                        customer_data.name,
                        customer_data.email, 
                        customer_data.phone
                    )
                    
                    if customer:
                        successful_customers.append(customer)
                        results.append(CustomerResult(
                            customer=customer,
                            success=True,
                            error=None,
                            input_data=input_data
                        ))
                        transaction.savepoint_commit(sid)
                    else:
                        has_errors = True
                        results.append(CustomerResult(
                            customer=None,
                            success=False,
                            error="; ".join(errors),
                            input_data=input_data
                        ))
                        transaction.savepoint_rollback(sid)
                        
                        if fail_on_error:
                            raise Exception(f"Failed to create customer {i+1}: {'; '.join(errors)}")
                
                except Exception as e:
                    transaction.savepoint_rollback(sid)
                    has_errors = True
                    results.append(CustomerResult(
                        customer=None,
                        success=False,
                        error=str(e),
                        input_data=input_data
                    ))
                    
                    if fail_on_error:
                        raise Exception(f"Failed to create customer {i+1}: {str(e)}")
        
        success_count = len(successful_customers)
        error_count = len(customers) - success_count
        total_count = len(customers)
        
        # Generate appropriate message
        if error_count == 0:
            message = f"Successfully created all {total_count} customers."
        elif success_count == 0:
            message = f"Failed to create any of the {total_count} customers."
        else:
            message = f"Processed {total_count} customers: {success_count} created, {error_count} failed."
        
        return BulkCreateCustomers(
            results=results,
            total_count=total_count,
            success_count=success_count,
            error_count=error_count,
            message=message,
            success=error_count == 0
        )

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock = graphene.Int()

    product = graphene.Field(ProductType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, name, price, stock=0):
        errors = []
        
        # Validate price - should be positive
        if price is None or price <= 0:
            errors.append("Price must be greater than 0")
        
        # Validate stock - should be non-negative (0 is allowed per requirements)
        if stock is not None and stock < 0:
            errors.append("Stock must be non-negative")
        
        # Set stock to 0 if not provided
        if stock is None:
            stock = 0

        if errors:
            raise Exception("; ".join(errors))
        
        try:
            product = Product.objects.create(name=name, price=price, stock=stock)
            return CreateProduct(
                product=product, 
                message="Product created successfully.",
                success=True
            )

        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime()

    order = graphene.Field(OrderType)
    message = graphene.String()
    success = graphene.Boolean()

    def mutate(self, info, customer_id, product_ids, order_date=None):
        errors = []
        
        # Validate customer_id
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            errors.append(f"Customer with ID {customer_id} does not exist")
            customer = None
        
        # Validate product_ids
        if not product_ids:
            errors.append("At least one product ID is required")
        else:
            # Check if all products exist
            products = Product.objects.filter(id__in=product_ids)
            existing_product_ids = set(str(p.id) for p in products)
            provided_product_ids = set(str(pid) for pid in product_ids)
            
            missing_ids = provided_product_ids - existing_product_ids
            if missing_ids:
                errors.append(f"Invalid product IDs: {', '.join(missing_ids)}")
        
        if errors:
            raise Exception("; ".join(errors))
        
        # Set order_date to now if not provided
        if order_date is None:
            order_date = timezone.now()
        
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
