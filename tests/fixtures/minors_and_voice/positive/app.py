class Profile:
    # campo de edad + embedding de voz: mezcla menor/voz (STT)
    age: int
    voice_embedding: bytes


def can_process(user: Profile):
    if user.age >= 16:
        return True
    return False