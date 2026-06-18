import logging
from typing import Any, Generic, Type, TypeVar

from django.core.exceptions import ValidationError
from django.db import models

from common.exceptions import NotFoundException, ValidationException

ModelT = TypeVar("ModelT", bound=models.Model)


class BaseService(Generic[ModelT]):
    """
    Base service class for business logic layers.

    Provides a built-in logger and helper methods for common create /
    read / update operations. Subclasses must declare a ``model``
    class attribute:

        class ProductService(BaseService[Product]):
            model = Product

    All ORM exceptions are translated to module exceptions so callers
    depend on a stable interface rather than ORM internals.
    """

    model: Type[ModelT]

    def __init__(self) -> None:
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    def _get_model(self) -> Type[ModelT]:
        if not getattr(self, "model", None):
            raise NotImplementedError(
                f"{self.__class__.__name__} must define a 'model' attribute "
                "or override '_get_model'."
            )
        return self.model

    def get_instance(self, pk: Any) -> ModelT:
        """
        Retrieve a model instance by primary key.

        Raises:
            NotFoundException: if no record with the given pk exists.
        """
        model_cls = self._get_model()
        try:
            return model_cls.objects.get(pk=pk)
        except model_cls.DoesNotExist as exc:
            self.logger.warning(
                "Failed to find %s with pk=%s", model_cls.__name__, pk
            )
            raise NotFoundException(
                f"{model_cls.__name__} with pk={pk} not found."
            ) from exc

    def update_instance(self, instance: ModelT, **fields: Any) -> ModelT:
        """
        Update specific fields on an instance, run full_clean, and save.

        Raises:
            ValidationException: if Django's full_clean fails.
        """
        updated_fields = []
        for field, value in fields.items():
            if hasattr(instance, field):
                setattr(instance, field, value)
                updated_fields.append(field)

        try:
            instance.full_clean()
        except ValidationError as exc:
            self.logger.error(
                "Validation error updating %s: %s", instance, exc.message_dict
            )
            raise ValidationException(
                "Validation failed", errors=exc.message_dict
            ) from exc

        instance.save(update_fields=updated_fields)
        self.logger.info("Updated %s fields: %s", instance, updated_fields)
        return instance

    def create_instance(self, **fields: Any) -> ModelT:
        """
        Instantiate, validate, and save a new model instance.

        Raises:
            ValidationException: if Django's full_clean fails.
        """
        model_cls = self._get_model()
        instance = model_cls(**fields)

        try:
            instance.full_clean()
        except ValidationError as exc:
            self.logger.error(
                "Validation error creating %s: %s",
                model_cls.__name__,
                exc.message_dict,
            )
            raise ValidationException(
                "Validation failed", errors=exc.message_dict
            ) from exc

        instance.save()
        self.logger.info("Created %s pk=%s", model_cls.__name__, instance.pk)
        return instance
