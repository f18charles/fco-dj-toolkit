"""
Tests for common.factories.

Verifies that BaseFactory, SoftDeletedTrait, and InactiveTrait work
correctly when applied to a concrete model.
"""
from django.db import connection, models
from django.test import TransactionTestCase

import factory

from common.factories import BaseFactory, InactiveTrait, SoftDeletedTrait
from common.mixins import SoftDeleteMixin, TimestampMixin


# ---------------------------------------------------------------------------
# Concrete test-only model and factory
# ---------------------------------------------------------------------------

class Widget(TimestampMixin, SoftDeleteMixin, models.Model):
    name = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "common"


class WidgetFactory(BaseFactory):
    class Meta:
        model = Widget

    name = factory.Sequence(lambda n: f"widget-{n}")
    is_active = True

    class Params:
        deleted = SoftDeletedTrait()
        inactive = InactiveTrait()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class BaseFactoryTestCase(TransactionTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_models = [Widget]
        with connection.schema_editor() as se:
            tables = connection.introspection.table_names()
            for m in cls.test_models:
                if m._meta.db_table not in tables:
                    se.create_model(m)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as se:
            tables = connection.introspection.table_names()
            for m in cls.test_models:
                if m._meta.db_table in tables:
                    se.delete_model(m)
        super().tearDownClass()

    def test_base_factory_creates_instance(self):
        widget = WidgetFactory()
        self.assertIsNotNone(widget.pk)
        self.assertTrue(widget.is_active)
        self.assertFalse(widget.is_deleted)

    def test_factory_build_does_not_hit_database(self):
        widget = WidgetFactory.build()
        self.assertIsNone(widget.pk)

    def test_soft_deleted_trait(self):
        widget = WidgetFactory(deleted=True)
        self.assertTrue(widget.is_deleted)
        self.assertIsNotNone(widget.deleted_at)

    def test_inactive_trait(self):
        widget = WidgetFactory(inactive=True)
        self.assertFalse(widget.is_active)

    def test_sequence_produces_unique_names(self):
        a = WidgetFactory()
        b = WidgetFactory()
        self.assertNotEqual(a.name, b.name)

    def test_factory_batch(self):
        widgets = WidgetFactory.create_batch(3)
        self.assertEqual(len(widgets), 3)
        names = {w.name for w in widgets}
        self.assertEqual(len(names), 3)  # all unique via Sequence
