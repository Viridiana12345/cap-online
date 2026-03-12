from django.contrib import admin
from .models import DoctorProfile, PatientProfile, Appointment, ChatMessage, CallRequest, CallSignal


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "especialidad",
        "cedula",
        "telefono",
        "modalidad",
        "duracion_sesion",
        "activo",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "especialidad",
        "cedula",
    )
    list_filter = ("activo", "modalidad", "especialidad")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "created_at", "is_read")
    search_fields = ("sender__username", "receiver__username", "text")
    list_filter = ("is_read", "created_at")


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "telefono")
    search_fields = ("user__first_name", "user__last_name", "user__email", "telefono")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "start_at", "end_at", "status")
    list_filter = ("status", "start_at")
    search_fields = (
        "patient__first_name",
        "patient__last_name",
        "doctor__first_name",
        "doctor__last_name",
    )


@admin.register(CallRequest)
class CallRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "doctor", "call_type", "status", "created_at")
    list_filter = ("status", "call_type", "created_at")


@admin.register(CallSignal)
class CallSignalAdmin(admin.ModelAdmin):
    list_display = ("room_key", "sender", "id")