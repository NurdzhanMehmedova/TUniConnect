from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import User, Role
from academics.models import Student, Specialty
import re
from academics.models import Department, Position
from django.contrib.auth import authenticate


class RegisterForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput,
        validators=[validate_password],
        label="Парола"
    )

    faculty_number = forms.CharField(required=False)
    year_of_study = forms.IntegerField(required=False)
    specialty = forms.ModelChoiceField(
        queryset=Specialty.objects.all(),
        required=False
    )

    role = forms.ModelChoiceField(
        queryset=Role.objects.exclude(name="SUPER_ADMIN")
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False
    )

    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        required=False
    )

    company_name = forms.CharField(
        required=False,
        max_length=100
    )

    contact_person = forms.CharField(
        required=False,
        max_length=50
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "phone",
            "password",
            "role",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "placeholder": " "
            })

        self.fields["role"].label_from_instance = lambda obj: obj.display_name()

        self.fields["faculty_number"].widget.attrs.update({
            "maxlength": 8,
            "inputmode": "numeric",
            "pattern": r"\d{8}"
        })

        self.fields["year_of_study"].widget.attrs.update({
            "min": 1,
            "max": 6,
            "type": "number"
        })

        self.fields["company_name"].widget.attrs.update({
            "maxlength": 100
        })

        self.fields["contact_person"].widget.attrs.update({
            "maxlength": 50
        })

        if 'department' in self.data:
            try:
                department_id = int(self.data.get('department'))
                self.fields['specialty'].queryset = Specialty.objects.filter(
                    department_id=department_id
                )
            except (ValueError, TypeError):
                pass
        else:
            self.fields['specialty'].queryset = Specialty.objects.none()

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")

        if not re.match(r"^[A-Za-zА-Яа-яЁё]{2,30}$", first_name):
            raise forms.ValidationError(
                "Името трябва да съдържа само букви и да е между 2 и 30 символа."
            )

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")

        if not re.match(r"^[A-Za-zА-Яа-яЁё]{2,30}$", last_name):
            raise forms.ValidationError(
                "Фамилията трябва да съдържа само букви и да е между 2 и 30 символа."
            )

        return last_name

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if not re.match(r"^[A-Za-z][A-Za-z0-9_]{3,19}$", username):
            raise forms.ValidationError(
                "Потребителското име трябва да започва с буква и да съдържа 4-20 символа (букви, цифри или _)."
            )

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Това потребителско име вече съществува.")

        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Този имейл вече е регистриран.")

        # Блокиране на fake домейни (пример)
        blocked_domains = ["mailinator.com", "tempmail.com"]

        domain = email.split("@")[-1]
        if domain.lower() in blocked_domains:
            raise forms.ValidationError("Този имейл домейн не е позволен.")

        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")

        if not re.match(r"^\+359\d{9}$", phone):
            raise forms.ValidationError(
                "Телефонът трябва да бъде във формат +359XXXXXXXXX."
            )

        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError(
                "Телефонният номер вече е регистриран."
            )

        valid_prefixes = ["87", "88", "89", "98", "99"]

        numbers = phone.replace("+359", "")

        if not numbers.startswith("8"):
            raise forms.ValidationError("Невалиден мобилен номер.")

        if numbers[:2] not in valid_prefixes:
            raise forms.ValidationError("Невалиден мобилен оператор.")

        return phone

    def clean_password(self):
        password = self.cleaned_data.get("password")

        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError(
                "Паролата трябва да съдържа поне една главна буква."
            )

        if not re.search(r"[a-z]", password):
            raise forms.ValidationError(
                "Паролата трябва да съдържа поне една малка буква."
            )

        if not re.search(r"\d", password):
            raise forms.ValidationError(
                "Паролата трябва да съдържа поне една цифра."
            )

        if not re.search(r"[!@#$%^&*()_+=\-]", password):
            raise forms.ValidationError(
                "Паролата трябва да съдържа поне един специален символ."
            )

        return password

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")

        # Вземаме ги веднъж тук
        faculty_number = cleaned_data.get("faculty_number")
        year = cleaned_data.get("year_of_study")
        department = cleaned_data.get("department")
        specialty = cleaned_data.get("specialty")
        position = cleaned_data.get("position")

        # ================= STUDENT =================
        if role and role.name == "STUDENT":

            if not faculty_number or not re.match(r"^\d{8}$", faculty_number):
                self.add_error(
                    "faculty_number",
                    "Факултетният номер трябва да съдържа точно 8 цифри."
                )

            if year is None or year < 1 or year > 6:
                self.add_error(
                    "year_of_study",
                    "Курсът трябва да бъде между 1 и 6."
                )

            if not department:
                self.add_error("department", "Изберете катедра.")

            if not specialty:
                self.add_error("specialty", "Изберете специалност.")

            if specialty and department:
                if specialty.department != department:
                    self.add_error(
                        "specialty",
                        "Невалидна специалност за избраната катедра."
                    )

        # ================= MENTOR =================
        if role and role.name == "MENTOR":

            if not department:
                self.add_error("department", "Изберете катедра.")

            if not position:
                self.add_error("position", "Изберете длъжност.")

        # ================= COMPANY =================
        if role and role.name == "COMPANY":

            if not cleaned_data.get("company_name"):
                self.add_error("company_name", "Въведете име на фирма.")

            if not cleaned_data.get("contact_person"):
                self.add_error("contact_person", "Въведете лице за контакт.")

        return cleaned_data


class LoginForm(forms.Form):

    username = forms.CharField(
        label="Потребителско име",
        widget=forms.TextInput(attrs={"placeholder": " "})
    )

    password = forms.CharField(
        label="Парола",
        widget=forms.PasswordInput(attrs={"placeholder": " "})
    )

    def clean(self):
        cleaned_data = super().clean()

        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)

            if not user:
                raise forms.ValidationError(
                    "Невалидно потребителско име или парола."
                )

            if not user.is_active:
                raise forms.ValidationError(
                    "Този акаунт е деактивиран."
                )

            cleaned_data["user"] = user

        return cleaned_data