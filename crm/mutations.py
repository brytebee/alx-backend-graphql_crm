# crm/mutations.py
import re
import graphene
from .models import Customer
from .serializers import CustomerSerializer

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerSerializer)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        # validate email
        if Customer.objects.filter(email=email).exists():
            raise graphene.Error("Email already exist.")
        
        # validate phone
        if phone and not re.match(r'^\+[0-9]\d{1,14}$', phone):
            raise graphene.Error("Invalid phone format")
        
        # create customer
        customer = Customer.objects.create(name=name, email=email, phone=phone)

        # return customer
        return CreateCustomer(customer=customer, message="Customer created successfully.")
