from django import forms
from django.contrib.auth.models import User

from .models import DoctorProfile, PatientProfile, Appointment


class DoctorCreateForm(forms.Form):
    """Formulario tipo RH para dar de alta doctores."""

    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    email = forms.EmailField(label="Correo")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)

    especialidad = forms.CharField(label="Especialidad", max_length=120, required=False)
    cedula = forms.CharField(label="Cédula", max_length=50, required=False)
    experiencia_anios = forms.IntegerField(label="Años de experiencia", min_value=0, required=False)
    biografia = forms.CharField(label="Biografía", widget=forms.Textarea(attrs={"rows": 4}), required=False)
    foto = forms.ImageField(label="Foto", required=False)
    activo = forms.BooleanField(label="Activo", required=False, initial=True)

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Ese correo ya está registrado.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned


class DoctorProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ["especialidad", "cedula", "experiencia_anios", "biografia", "foto", "activo"]
        widgets = {
            "biografia": forms.Textarea(attrs={"rows": 4}),
        }


class PatientProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ["telefono", "biografia"]
        widgets = {
            "biografia": forms.Textarea(attrs={"rows": 4}),
        }


class AppointmentCreateForm(forms.ModelForm):
    """Formulario para que el paciente solicite una cita."""

    start_at = forms.DateTimeField(
        label="Inicio",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    end_at = forms.DateTimeField(
        label="Fin",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    class Meta:
        model = Appointment
        fields = ["doctor", "start_at", "end_at", "notes"]

