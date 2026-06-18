import logging
from typing import Any, Generic, Type, TypeVar
from django.core.exceptions import ValidationError
from django.db import models
from common.exceptions import ValidationException

ModelT = TypeVar("ModelT", bound=models.Model)


class BaseService(Generic[ModelT]):
    """
    Base service class for business logic layers.
    Provides a built-in logger and helper methods for querying and updating.
    """

    model: Type[ModelT]

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def _get_model(self) -> Type[ModelT]:
        if not getattr(self, "model", None):
            raise NotImplementedError(
                f"{self.__class__.__name__} must define a 'model' attribute or override '_get_model'."
            )
        return self.model

    def get_instance(self, pk: Any) -> ModelT:
        """
        Retrieve a model instance by primary key.
        """
        model_cls = self._get_model()
        try:
            return model_cls.objects.get(pk=pk)
        except model_cls.DoesNotExist:
            self.logger.warning("Failed to find %s instance with pk: %s", model_cls.__name__, pk)
            raise

    def update_instance(self, instance: ModelT, **fields: Any) -> ModelT:
        """
        Update specific fields of an instance, run full_clean, and save.
        """
        updated_fields = []
        for field, value in fields.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
                updated_fields.append(field)

        try:
            instance.full_clean()
        except ValidationError as e:
            self.logger.error("Validation error during update of %s: %s", instance, e.message_dict)
            raise ValidationException("Validation failed", errors=e.message_dict)

        instance.save(update_fields=updated_fields)
        self.logger.info("Updated %s with fields: %s", instance, updated_fields)
        return instance

    def create_instance(self, **fields: Any) -> ModelT:
        """
        Instantiate, clean, and save a new model instance.
        """
        model_cls = self._get_model()
        instance = model_cls(**fields)

        try:
            instance.full_clean()
        except ValidationError as e:
            self.logger.error("Validation error during creation of %s: %s", model_cls.__name__, e.message_dict)
            raise ValidationException("Validation failed", errors=e.message_dict)

        instance.save()
        self.logger.info("Created %s instance: %s", model_cls.__name__, instance.pk)
        return instance
