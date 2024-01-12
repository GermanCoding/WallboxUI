from django.contrib.auth.hashers import PBKDF2PasswordHasher


class TunedPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """
    A subclass of PBKDF2PasswordHasher that uses a configurable amount of iterations
    """

    iterations = HASH_ITERATIONS