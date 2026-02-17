from django.db import models
from django.contrib.postgres.fields import JSONField
"""
In Django, the GinIndex class is a PostgreSQL-specific index used for efficiently querying 
composite values like array fields, JSONField, and full-text search vector fields. 
"""
from django.contrib.postgres.indexes import GinIndex


