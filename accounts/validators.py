import re
from django.core.exceptions import ValidationError


class CustomPasswordValidator:
    def validate(self, password, user=None):

        if len(password) < 8:
            raise ValidationError(
                "Паролата трябва да бъде минимум 8 символа."
            )

        if not re.search(r'[A-Za-z]', password):
            raise ValidationError(
                "Паролата трябва да съдържа поне една буква."
            )

        if not re.search(r'\d', password):
            raise ValidationError(
                "Паролата трябва да съдържа поне една цифра."
            )

    def get_help_text(self):
        return "Паролата трябва да е минимум 8 символа и да съдържа букви и цифри."