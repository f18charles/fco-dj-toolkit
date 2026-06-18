import uuid
from django.contrib.auth import get_user_model
from django.db import connection, models
from django.test import TransactionTestCase
from django.utils import timezone
from common.models import AuditFieldsModel, SoftDeleteModel, TimestampedModel, UUIDModel
from common.services import BaseService
from common.exceptions import ValidationException

User = get_user_model()


class ConcreteTimestampedModel(TimestampedModel):
    class Meta:
        app_label = "common"


class ConcreteUUIDModel(UUIDModel):
    class Meta:
        app_label = "common"


class ConcreteSoftDeleteModel(SoftDeleteModel):
    name = models.CharField(max_length=50, blank=True)

    class Meta:
        app_label = "common"


class ConcreteAuditFieldsModel(AuditFieldsModel):
    class Meta:
        app_label = "common"


class ConcreteServiceSoftDeleteModel(SoftDeleteModel):
    name = models.CharField(max_length=50, blank=True)

    class Meta:
        app_label = "common"


class ConcreteService(BaseService[ConcreteServiceSoftDeleteModel]):
    model = ConcreteServiceSoftDeleteModel


class ModelsTestCase(TransactionTestCase):
    """
    Test cases for abstract models using concrete test-only model subclasses.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create database tables safely if they do not exist
        cls.test_models = [
            ConcreteTimestampedModel,
            ConcreteUUIDModel,
            ConcreteSoftDeleteModel,
            ConcreteAuditFieldsModel,
        ]
        with connection.schema_editor() as schema_editor:
            tables = connection.introspection.table_names()
            for model in cls.test_models:
                if model._meta.db_table not in tables:
                    schema_editor.create_model(model)

    @classmethod
    def tearDownClass(cls):
        # Drop database tables safely if they exist
        with connection.schema_editor() as schema_editor:
            tables = connection.introspection.table_names()
            for model in cls.test_models:
                if model._meta.db_table in tables:
                    schema_editor.delete_model(model)
        super().tearDownClass()

    def test_timestamped_model(self):
        obj = ConcreteTimestampedModel.objects.create()
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.updated_at)
        orig_created = obj.created_at
        orig_updated = obj.updated_at

        # Test updating updates only updated_at
        obj.save()
        obj.refresh_from_db()
        self.assertEqual(obj.created_at, orig_created)
        self.assertGreaterEqual(obj.updated_at, orig_updated)

    def test_uuid_model(self):
        obj = ConcreteUUIDModel.objects.create()
        self.assertIsInstance(obj.id, uuid.UUID)
        self.assertEqual(ConcreteUUIDModel.objects.filter(id=obj.id).count(), 1)

    def test_soft_delete_model(self):
        obj1 = ConcreteSoftDeleteModel.objects.create(name="Active 1")
        obj2 = ConcreteSoftDeleteModel.objects.create(name="Active 2")

        self.assertEqual(ConcreteSoftDeleteModel.objects.count(), 2)

        # Test instance delete override (soft delete)
        obj1.delete()
        self.assertTrue(obj1.is_deleted)
        self.assertIsNotNone(obj1.deleted_at)

        # Active queryset shouldn't contain it
        self.assertEqual(ConcreteSoftDeleteModel.objects.count(), 1)
        self.assertEqual(ConcreteSoftDeleteModel.objects.filter(pk=obj1.pk).count(), 0)

        # all_objects manager should contain it
        self.assertEqual(ConcreteSoftDeleteModel.all_objects.count(), 2)
        self.assertEqual(ConcreteSoftDeleteModel.all_objects.filter(pk=obj1.pk).count(), 1)

        # Test restore
        obj1.restore()
        self.assertFalse(obj1.is_deleted)
        self.assertIsNone(obj1.deleted_at)
        self.assertEqual(ConcreteSoftDeleteModel.objects.count(), 2)

        # Test QuerySet delete override (soft delete)
        ConcreteSoftDeleteModel.objects.all().delete()
        self.assertEqual(ConcreteSoftDeleteModel.objects.count(), 0)
        self.assertEqual(ConcreteSoftDeleteModel.all_objects.count(), 2)

        # Test QuerySet hard_delete
        ConcreteSoftDeleteModel.all_objects.all().hard_delete()
        self.assertEqual(ConcreteSoftDeleteModel.all_objects.count(), 0)

    def test_audit_fields_model(self):
        user1 = User.objects.create_user(username="creator", email="creator@example.com", password="password")
        user2 = User.objects.create_user(username="updater", email="updater@example.com", password="password")

        obj = ConcreteAuditFieldsModel.objects.create(created_by=user1, updated_by=user2)
        self.assertEqual(obj.created_by, user1)
        self.assertEqual(obj.updated_by, user2)


class BaseServiceTestCase(TransactionTestCase):
    """
    Test cases for BaseService functionality.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_models = [ConcreteServiceSoftDeleteModel]
        with connection.schema_editor() as schema_editor:
            tables = connection.introspection.table_names()
            for model in cls.test_models:
                if model._meta.db_table not in tables:
                    schema_editor.create_model(model)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            tables = connection.introspection.table_names()
            for model in cls.test_models:
                if model._meta.db_table in tables:
                    schema_editor.delete_model(model)
        super().tearDownClass()

    def setUp(self):
        self.service = ConcreteService()

    def test_service_create_instance(self):
        obj = self.service.create_instance(name="Created via Service")
        self.assertIsNotNone(obj.pk)
        self.assertEqual(obj.name, "Created via Service")

    def test_service_get_instance(self):
        obj = ConcreteServiceSoftDeleteModel.objects.create(name="Lookup Me")
        fetched = self.service.get_instance(obj.pk)
        self.assertEqual(fetched.name, "Lookup Me")

        with self.assertRaises(ConcreteServiceSoftDeleteModel.DoesNotExist):
            self.service.get_instance(999999)

    def test_service_update_instance(self):
        obj = ConcreteServiceSoftDeleteModel.objects.create(name="Initial Name")
        updated = self.service.update_instance(obj, name="New Name")
        self.assertEqual(updated.name, "New Name")
        self.assertEqual(ConcreteServiceSoftDeleteModel.objects.get(pk=obj.pk).name, "New Name")

    def test_service_validation_error(self):
        # We test that ValidationError is wrapped in ValidationException
        long_name = "a" * 51
        with self.assertRaises(ValidationException) as ctx:
            self.service.create_instance(name=long_name)

        self.assertIn("name", ctx.exception.errors)
