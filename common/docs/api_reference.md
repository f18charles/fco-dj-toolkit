# API Reference

This document provides documentation and usage examples for all components in the `common` module.

---

## 1. Abstract Models & Mixins

### TimestampedModel & TimestampMixin
Adds `created_at` (auto_now_add=True) and `updated_at` (auto_now=True) datetime fields to a model.

```python
from common.models import TimestampedModel
from django.db import models

class Article(TimestampedModel):
    title = models.CharField(max_length=100)
```

### UUIDModel
Changes the primary key from an auto-incrementing integer to a UUID4 key (`id`).

```python
from common.models import UUIDModel
from django.db import models

class Resource(UUIDModel):
    name = models.CharField(max_length=100)
```

### SoftDeleteModel & SoftDeleteMixin
Soft-deletes instances instead of permanently purging them from the database.

* Fields: `is_deleted` (bool), `deleted_at` (datetime)
* Default Manager: `objects` (filters out deleted items)
* Full Manager: `all_objects` (returns all items)
* Methods:
  - `delete()` / `soft_delete()`: Marks instance as deleted.
  - `restore()`: Restores deleted instance.
  - `hard_delete()`: Removes the instance from the database completely.

```python
from common.models import SoftDeleteModel

# Create
item = MyModel.objects.create(name="Item 1")

# Soft Delete (using .delete() or .soft_delete())
item.delete()

# Query only active items
active_items = MyModel.objects.all()

# Query all items (including deleted)
all_items = MyModel.all_objects.all()

# Restore
item.restore()
```

### AuditFieldsModel & UserTrackingMixin
Adds `created_by` and `updated_by` fields referencing `settings.AUTH_USER_MODEL`.

```python
from common.models import AuditFieldsModel

class Project(AuditFieldsModel):
    name = models.CharField(max_length=100)
```

---

## 2. Base Service Layer

### BaseService
Provides generic CRUD methods with logging and validation mapping out of the box.

```python
from common.services import BaseService
from myapp.models import MyModel

class MyModelService(BaseService[MyModel]):
    model = MyModel

service = MyModelService()

# Create (runs full_clean and handles validation error mapping)
obj = service.create_instance(name="Test")

# Retrieve
obj = service.get_instance(obj.pk)

# Update
service.update_instance(obj, name="New Name")
```

---

## 3. Exceptions

Located in `common.exceptions`:
* `FcoKitException`: Base exception.
* `ValidationException`: Raised when ORM/logic validation fails (exposes `errors` dict).
* `ServiceException`: Generic service layer failures.
* `NotFoundException`: Resource lookup failures.
* `PermissionException`: Authorization check failures.

---

## 4. Validators

Located in `common.validators`:
* `validate_username`: Ensures usernames match standard rules.
* `validate_slug`: Regex validator for lowercase slugs.
* `validate_phone_number`: Validates international E.164 phone numbers.
* `FileExtensionValidator(allowed_extensions=['pdf', 'png'])`: Deconstructible class validating uploaded file types.

```python
from django.db import models
from common.validators import FileExtensionValidator, validate_phone_number

class UserProfile(models.Model):
    phone = models.CharField(max_length=30, validators=[validate_phone_number])
    resume = models.FileField(validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
```

---

## 5. Utilities

Located in `common.utils`:
* `generate_uuid()`: Generates a random UUID4.
* `normalize_email(email)`: Trims whitespace and lowercases domain names.
* `safe_getattr(obj, path, default)`: Retrieve nested attributes via dot-notation.
* `chunk_list(lst, size)`: Split iterables into batches.

```python
from common.utils import safe_getattr, chunk_list

city = safe_getattr(user, "profile.address.city", default="Unknown")
batches = chunk_list([1, 2, 3, 4, 5], chunk_size=2)  # [[1, 2], [3, 4], [5]]
```
