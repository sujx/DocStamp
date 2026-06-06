"""Business logic layer — pure functions with zero Flask dependencies.

Each module is independently testable. All functions accept plain data and
return ServiceResult or raise ServiceError for the global handler to catch.
"""
