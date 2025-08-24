# crm/filters.py
import django_filters
from .models import Customer, Product, Order

class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', help_text="Case-insensitive partial match on name")
    email = django_filters.CharFilter(lookup_expr='icontains', help_text="Case-insensitive partial match on email")
    created_at = django_filters.DateTimeFromToRangeFilter(help_text="Filter by creation date range")
    created_at__gte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', help_text="Created after this date")
    created_at__lte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', help_text="Created before this date")
    
    # Custom filter for phone number pattern (starts with +1)
    phone_pattern = django_filters.CharFilter(method='filter_phone_pattern', help_text="Filter by phone pattern (e.g., starts with +1)")
    
    class Meta:
        model = Customer
        fields = ['name', 'email', 'created_at', 'phone_pattern']
    
    def filter_phone_pattern(self, queryset, name, value):
        """Custom filter method for phone pattern matching"""
        if value:
            return queryset.filter(phone__startswith=value)
        return queryset

class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', help_text="Case-insensitive partial match on name")
    price = django_filters.RangeFilter(help_text="Filter by price range")
    price__gte = django_filters.NumberFilter(field_name='price', lookup_expr='gte', help_text="Price greater than or equal")
    price__lte = django_filters.NumberFilter(field_name='price', lookup_expr='lte', help_text="Price less than or equal")
    stock = django_filters.NumberFilter(help_text="Exact stock match")
    stock__gte = django_filters.NumberFilter(field_name='stock', lookup_expr='gte', help_text="Stock greater than or equal")
    stock__lte = django_filters.NumberFilter(field_name='stock', lookup_expr='lte', help_text="Stock less than or equal")
    
    # Custom filter for low stock
    low_stock = django_filters.BooleanFilter(method='filter_low_stock', help_text="Filter products with stock < 10")
    
    class Meta:
        model = Product
        fields = ['name', 'price', 'stock', 'low_stock']
    
    def filter_low_stock(self, queryset, name, value):
        """Custom filter for products with low stock (< 10)"""
        if value:
            return queryset.filter(stock__lt=10)
        return queryset

class OrderFilter(django_filters.FilterSet):
    total_amount = django_filters.RangeFilter(help_text="Filter by total amount range")
    total_amount__gte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte', help_text="Total amount greater than or equal")
    total_amount__lte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte', help_text="Total amount less than or equal")
    order_date = django_filters.DateTimeFromToRangeFilter(help_text="Filter by order date range")
    order_date__gte = django_filters.DateTimeFilter(field_name='order_date', lookup_expr='gte', help_text="Ordered after this date")
    order_date__lte = django_filters.DateTimeFilter(field_name='order_date', lookup_expr='lte', help_text="Ordered before this date")
    
    # Filter by related customer name
    customer_name = django_filters.CharFilter(field_name='customer__name', lookup_expr='icontains', help_text="Filter by customer name")
    
    # Filter by related product name
    product_name = django_filters.CharFilter(field_name='products__name', lookup_expr='icontains', help_text="Filter by product name")
    
    # Filter by specific product ID
    product_id = django_filters.NumberFilter(field_name='products__id', help_text="Filter orders that include specific product ID")
    
    class Meta:
        model = Order
        fields = ['total_amount', 'order_date', 'customer_name', 'product_name', 'product_id']
