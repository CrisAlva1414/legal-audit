import logging

logging.basicConfig(level=logging.DEBUG)


class User:
    email: str
    phone: str


def process(user: User):
    logging.info(f"procesando {user.email} con tel {user.phone}")
    print(user)