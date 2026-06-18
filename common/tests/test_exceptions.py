from django.test import SimpleTestCase
from common.exceptions import (
    FcoKitException,
    NotFoundException,
    PermissionException,
    ServiceException,
    ValidationException,
)


class ExceptionsTestCase(SimpleTestCase):
    """
    Test cases for custom exceptions in the common module.
    """

    def test_base_exception(self):
        exc = FcoKitException("Base error message", code="custom_code")
        self.assertEqual(str(exc), "Base error message")
        self.assertEqual(exc.message, "Base error message")
        self.assertEqual(exc.code, "custom_code")

        # Test default code
        exc_default = FcoKitException("Default message")
        self.assertEqual(exc_default.code, "error")

    def test_validation_exception(self):
        errors_dict = {"email": ["Invalid email format"]}
        exc = ValidationException("Validation failed", errors=errors_dict)
        self.assertEqual(exc.message, "Validation failed")
        self.assertEqual(exc.code, "validation_error")
        self.assertEqual(exc.errors, errors_dict)

        # Test empty errors default
        exc_default = ValidationException("Failed")
        self.assertEqual(exc_default.errors, {})

    def test_service_exception(self):
        exc = ServiceException("Service failed")
        self.assertEqual(exc.message, "Service failed")
        self.assertEqual(exc.code, "service_error")
        self.assertTrue(isinstance(exc, FcoKitException))

    def test_not_found_exception(self):
        exc = NotFoundException("Item not found")
        self.assertEqual(exc.message, "Item not found")
        self.assertEqual(exc.code, "not_found")
        self.assertTrue(isinstance(exc, FcoKitException))

    def test_permission_exception(self):
        exc = PermissionException("Access denied")
        self.assertEqual(exc.message, "Access denied")
        self.assertEqual(exc.code, "permission_denied")
        self.assertTrue(isinstance(exc, FcoKitException))
