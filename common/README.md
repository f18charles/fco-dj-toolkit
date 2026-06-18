# FCO Django Kit - Common Module

The `common` module serves as the foundational utility layer for all other modules in the **FCO Django Kit**. It provides reusable abstract models, mixins, exceptions, validators, choices, and utilities.

## Directory Structure

```
common/
 admin.py          # Generic base admin classes
 apps.py           # App configuration
 choices.py        # Reusable TextChoices
 constants.py      # Common constraints and defaults
 exceptions.py     # Base Exception hierarchy
 types.py          # Type aliases
 utils.py          # Helper functions (normalize_email, chunk_list, safe_getattr)
 validators.py     # File, Phone, Username and Slug validators
 services.py       # Generic BaseService class
 mixins/           # Database Model Mixins
 models/           # Abstract Database Models
 tests/            # Test Suite
 docs/             # Technical architecture guides & API Reference
```

## Installation

Add `'common.apps.CommonConfig'` to your Django settings:

```python
INSTALLED_APPS = [
    # ...
    'common.apps.CommonConfig',
    # ...
]
```

## Quick Start Examples

### Using abstract models
```python
from django.db import models
from common.models import UUIDModel, TimestampedModel, SoftDeleteModel

class Product(UUIDModel, TimestampedModel, SoftDeleteModel):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

### Using BaseService
```python
from common.services import BaseService
from .models import Product

class ProductService(BaseService[Product]):
    model = Product

# Automatically validates product attributes and saves
service = ProductService()
product = service.create_instance(name="Coffee Maker", price=49.99)
```

## Detailed Documentation

For advanced setup and API lists, see:
* [Architecture and Design Decisions](docs/architecture.md)
* [API Reference](docs/api_reference.md)
