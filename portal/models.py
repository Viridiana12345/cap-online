from django.db import models
from django.contrib.auth.models import User


class PatientProfile(models.Model):
    """Datos extra para pacientes."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    telefono = models.CharField(max_length=30, blank=True)
    biografia = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PatientProfile({self.user.username})"


class DoctorProfile(models.Model):
    MODALIDAD_CHOICES = [
        ("online", "Online"),
        ("presencial", "Presencial"),
        ("ambos", "Online y Presencial"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="doctor_profile"
    )
    especialidad = models.CharField(max_length=120)
    cedula = models.CharField(max_length=80)
    biografia = models.TextField(blank=True)
    experiencia_anios = models.IntegerField(default=0)

    # NUEVOS CAMPOS
    telefono = models.CharField(max_length=20, blank=True)
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES, default="online")
    duracion_sesion = models.PositiveIntegerField(default=60, help_text="Duración en minutos")
    horario_inicio = models.TimeField(blank=True, null=True)
    horario_fin = models.TimeField(blank=True, null=True)
    idiomas = models.CharField(max_length=120, blank=True, help_text="Ej. Español, Inglés")
    costo_consulta = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    foto = models.ImageField(upload_to="doctores/", blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.especialidad}"


class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.text[:20]}"


class CallRequest(models.Model):
    CALL_TYPES = (
        ("audio", "Audio"),
        ("video", "Video"),
    )
    STATUS = (
        ("pending", "Pendiente"),
        ("approved", "Aprobada"),
        ("rejected", "Rechazada"),
        ("done", "Realizada"),
    )

    # paciente
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="call_requests")
    # doctor asignado
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_calls")
    call_type = models.CharField(max_length=10, choices=CALL_TYPES, default="audio")
    scheduled_for = models.DateTimeField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.call_type} - {self.status}"


class Appointment(models.Model):
    STATUS = (
        ("pending", "Pendiente"),
        ("approved", "Aprobada"),
        ("rejected", "Rechazada"),
        ("done", "Realizada"),
    )

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointments_as_patient")
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointments_as_doctor")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    notes = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_at"]

    def __str__(self):
        return f"{self.patient.username} -> {self.doctor.username} @ {self.start_at} ({self.status})"


class CallSignal(models.Model):
    """Señalización simple (SDP/ICE) para WebRTC usando polling."""
    room_key = models.CharField(max_length=80, db_index=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]