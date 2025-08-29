#!/bin/bash
# Delete inactive customers with no orders since a year ago

timestamp=$(date +"%Y-%m-%d %H:%M:%S")
deleted=$(echo "
from datetime import timedelta
from django.utils import timezone
from crm.models import Customer
cutoff = timezone.now() - timedelta(days=365)
qs = Customer.objects.filter(orders__isnull=True, created_at__lt=cutoff)
count = qs.count()
qs.delete()
print(count)
" | python manage.py shell | tail -n 1)

echo "$timestamp - Deleted $deleted inactive customers" >> /tmp/customer_cleanup_log.txt

# chmod +x crm/cron_jobs/clean_inactive_customers.sh
