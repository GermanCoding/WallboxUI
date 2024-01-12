from django.contrib.auth.hashers import PBKDF2PasswordHasher

from backend.settings import HASH_ITERATIONS


class TunedPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """
    A subclass of PBKDF2PasswordHasher that uses a configurable amount of iterations
    """

    iterations = HASH_ITERATIONS
