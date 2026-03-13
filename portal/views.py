from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.http import HttpResponse

from .models import ChatMessage, CallRequest, DoctorProfile, PatientProfile, Appointment, CallSignal
from .forms import (
    DoctorCreateForm,
    DoctorProfileUpdateForm,
    PatientProfileUpdateForm,
    AppointmentCreateForm,
)


def landing(request):
    doctores = DoctorProfile.objects.filter(
        activo=True
    ).select_related("user").order_by(
        "user__first_name",
        "user__last_name"
    )

    return render(request, "index.html", {
        "doctores": doctores
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect("portal_dashboard")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        user = authenticate(request, username=email, password=password)
        if user is None:
            messages.error(request, "Correo o contraseña incorrectos.")
            return redirect("landing")

        login(request, user)
        messages.success(request, "Sesión iniciada correctamente.")
        return redirect("portal_dashboard")

    return render(request, "auth/login.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect("portal_dashboard")

    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        telefono = (request.POST.get("telefono") or "").strip()
        biografia = (request.POST.get("biografia") or "").strip()

        parts = [p for p in full_name.split(" ") if p]
        first_name = parts[0] if parts else ""
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        password2 = request.POST.get("password2") or ""

        if not full_name or not email or not password:
            messages.error(request, "Completa todos los campos.")
            return redirect("signup")

        if password != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("signup")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Ese correo ya está registrado. Inicia sesión.")
            return redirect("login")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        pacientes = _ensure_group("Pacientes")
        user.groups.add(pacientes)
        PatientProfile.objects.create(user=user, telefono=telefono, biografia=biografia)

        messages.success(request, "Registrado correctamente. Ahora inicia sesión.")
        return redirect("login")

    return render(request, "auth/register.html")


def logout_view(request):
    logout(request)
    messages.success(request, "Sesión cerrada.")
    return redirect("login")


def _is_admin(user: User) -> bool:
    return user.is_staff or user.is_superuser


def _is_doctor(user: User) -> bool:
    doctors_group = _ensure_group("Doctores")
    return doctors_group in user.groups.all()


def _notifications_count(user: User) -> int:
    unread_messages_count = ChatMessage.objects.filter(receiver=user, is_read=False).count()
    if _is_doctor(user):
        pending_calls_count = CallRequest.objects.filter(doctor=user, status="pending").count()
        pending_appts = Appointment.objects.filter(doctor=user, status="pending").count()
    else:
        pending_calls_count = CallRequest.objects.filter(user=user, status="pending").count()
        pending_appts = Appointment.objects.filter(patient=user, status="pending").count()
    return unread_messages_count + pending_calls_count + pending_appts


def _ensure_group(name: str) -> Group:
    group, _ = Group.objects.get_or_create(name=name)
    return group


@login_required(login_url="login")
def dashboard(request):
    unread_messages_count = ChatMessage.objects.filter(receiver=request.user, is_read=False).count()
    if _is_doctor(request.user):
        pending_calls_count = CallRequest.objects.filter(doctor=request.user, status="pending").count()
        pending_appts_count = Appointment.objects.filter(doctor=request.user, status="pending").count()
    else:
        pending_calls_count = CallRequest.objects.filter(user=request.user, status="pending").count()
        pending_appts_count = Appointment.objects.filter(patient=request.user, status="pending").count()

    ctx = {
        "notifications_count": _notifications_count(request.user),
        "unread_messages_count": unread_messages_count,
        "pending_calls_count": pending_calls_count,
        "pending_appts_count": pending_appts_count,
        "is_doctor": _is_doctor(request.user),
    }
    return render(request, "portal/dashboard.html", ctx)


@login_required(login_url="login")
def notifications(request):
    unread = ChatMessage.objects.filter(receiver=request.user, is_read=False).order_by("-created_at")[:20]
    if _is_doctor(request.user):
        calls = CallRequest.objects.filter(doctor=request.user).order_by("-created_at")[:20]
        appts = Appointment.objects.filter(doctor=request.user).order_by("-created_at")[:20]
    else:
        calls = CallRequest.objects.filter(user=request.user).order_by("-created_at")[:20]
        appts = Appointment.objects.filter(patient=request.user).order_by("-created_at")[:20]

    ctx = {
        "notifications_count": _notifications_count(request.user),
        "unread_messages": unread,
        "call_requests": calls,
        "appointments": appts,
        "is_doctor": _is_doctor(request.user),
    }
    return render(request, "portal/notifications.html", ctx)


@login_required(login_url="login")
def specialists(request):
    doctores = DoctorProfile.objects.filter(activo=True).select_related("user").order_by("user__first_name", "user__last_name")
    ctx = {
        "notifications_count": _notifications_count(request.user),
        "doctores": doctores,
    }
    return render(request, "portal/specialists.html", ctx)


@login_required(login_url="login")
def profile(request, doctor_id: int):
    doctor = get_object_or_404(DoctorProfile.objects.select_related("user"), pk=doctor_id, activo=True)
    ctx = {
        "notifications_count": _notifications_count(request.user),
        "doctor": doctor,
    }
    return render(request, "portal/profile.html", ctx)


@login_required(login_url="login")
def calendar_view(request):
    if _is_doctor(request.user):
        return redirect("portal_calendar_doctor")
    return redirect("portal_calendar_patient")


@login_required(login_url="login")
def calendar_patient(request):
    if _is_doctor(request.user):
        return redirect("portal_calendar_doctor")

    form = AppointmentCreateForm()
    form.fields["doctor"].queryset = User.objects.filter(doctor_profile__activo=True).order_by(
        "first_name", "last_name"
    )

    appts = Appointment.objects.filter(patient=request.user).select_related("doctor")
    ctx = {
        "notifications_count": _notifications_count(request.user),
        "form": form,
        "appointments": appts,
    }
    return render(request, "portal/calendar_patient.html", ctx)


@login_required(login_url="login")
def calendar_doctor(request):
    if not _is_doctor(request.user):
        return redirect("portal_calendar_patient")

    appts = Appointment.objects.filter(doctor=request.user).select_related("patient")
    ctx = {
        "notifications_count": _notifications_count(request.user),
        "appointments": appts,
    }
    return render(request, "portal/calendar_doctor.html", ctx)


@login_required(login_url="login")
def calls(request):
    if _is_doctor(request.user):
        my_calls = CallRequest.objects.filter(doctor=request.user).select_related("user", "doctor")
    else:
        my_calls = CallRequest.objects.filter(user=request.user).select_related("user", "doctor")

    ctx = {
        "notifications_count": _notifications_count(request.user),
        "my_calls": my_calls,
        "is_doctor": _is_doctor(request.user),
        "doctores": DoctorProfile.objects.filter(activo=True).select_related("user").order_by(
            "user__first_name", "user__last_name"
        ),
    }
    return render(request, "portal/calls.html", ctx)


@login_required(login_url="login")
def chat(request, user_id=None):
    me = request.user
    doctors_group = _ensure_group("Doctores")
    is_doctor = _is_doctor(me)

    if is_doctor:
        contactos = User.objects.exclude(id=me.id).exclude(groups=doctors_group).order_by("first_name", "last_name", "username")
    else:
        contactos = User.objects.filter(doctor_profile__activo=True).order_by("first_name", "last_name", "username")

    receiver = None
    thread = []
    if user_id:
        receiver = get_object_or_404(User, pk=user_id)
        thread = ChatMessage.objects.filter(
            Q(sender=me, receiver=receiver) | Q(sender=receiver, receiver=me)
        ).order_by("created_at")
        ChatMessage.objects.filter(sender=receiver, receiver=me, is_read=False).update(is_read=True)

    ctx = {
        "notifications_count": _notifications_count(request.user),
        "users": contactos,
        "receiver": receiver,
        "thread": thread,
    }
    return render(request, "portal/chat.html", ctx)


@login_required(login_url="login")
def send_message(request, user_id: int):
    if request.method != "POST":
        return redirect("portal_chat")

    text = (request.POST.get("text") or "").strip()

    if not text:
        messages.error(request, "Escribe un mensaje antes de enviar.")
        return redirect("portal_chat_with", user_id=user_id)

    receiver = get_object_or_404(User, pk=user_id)
    ChatMessage.objects.create(sender=request.user, receiver=receiver, text=text)
    return redirect("portal_chat_with", user_id=receiver.id)


@login_required(login_url="login")
def chat_thread_api(request, user_id: int):
    me = request.user
    other = get_object_or_404(User, pk=user_id)

    try:
        after_id = int(request.GET.get("after", "0"))
    except ValueError:
        after_id = 0

    qs = ChatMessage.objects.filter(
        Q(sender=me, receiver=other) | Q(sender=other, receiver=me)
    ).order_by("id")

    if after_id:
        qs = qs.filter(id__gt=after_id)

    items = [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "text": m.text,
            "created_at": m.created_at.isoformat(),
        }
        for m in qs[:200]
    ]

    ChatMessage.objects.filter(sender=other, receiver=me, is_read=False).update(is_read=True)
    return JsonResponse({"messages": items})


@login_required(login_url="login")
@require_POST
def chat_send_api(request, user_id: int):
    other = get_object_or_404(User, pk=user_id)
    text = (request.POST.get("text") or "").strip()

    if not text:
        return HttpResponseBadRequest("missing text")

    msg = ChatMessage.objects.create(sender=request.user, receiver=other, text=text)
    return JsonResponse({"ok": True, "id": msg.id})


@login_required(login_url="login")
def request_call(request):
    if request.method != "POST":
        return redirect("portal_calls")

    call_type = request.POST.get("call_type", "audio")
    doctor_id = request.POST.get("doctor_id")
    notes = (request.POST.get("notes") or "").strip()

    if call_type not in ("audio", "video"):
        call_type = "audio"

    doctor = None
    if doctor_id:
        try:
            doctor = User.objects.get(pk=int(doctor_id), doctor_profile__activo=True)
        except Exception:
            doctor = None

    if not doctor:
        messages.error(request, "Selecciona un doctor válido.")
        return redirect("portal_calls")

    CallRequest.objects.create(
        user=request.user,
        doctor=doctor,
        call_type=call_type,
        notes=notes
    )
    messages.success(request, "Solicitud de llamada enviada.")
    return redirect("portal_calls")


@login_required(login_url="login")
@require_POST
def call_update_status(request, call_id: int, new_status: str):
    call = get_object_or_404(CallRequest, pk=call_id)

    if not _is_doctor(request.user) or call.doctor_id != request.user.id:
        return HttpResponseBadRequest("not allowed")

    if new_status not in ("approved", "rejected", "done"):
        return HttpResponseBadRequest("bad status")

    call.status = new_status
    call.save(update_fields=["status"])

    return redirect("portal_calls")


@login_required(login_url="login")
def call_status_api(request):
    if _is_doctor(request.user):
        qs = CallRequest.objects.filter(doctor=request.user).select_related("user", "doctor").order_by("-created_at")
    else:
        qs = CallRequest.objects.filter(user=request.user).select_related("user", "doctor").order_by("-created_at")

    items = []
    for c in qs[:20]:
        items.append({
            "id": c.id,
            "status": c.status,
            "call_type": c.call_type,
            "call_type_display": c.get_call_type_display(),
            "created_at": c.created_at.strftime("%d/%m/%Y %H:%M"),
            "notes": c.notes or "",
            "user_name": c.user.get_full_name() or c.user.username,
            "doctor_name": (c.doctor.get_full_name() or c.doctor.username) if c.doctor else "",
            "room_url": f"/portal/call/{c.id}/room/" if c.status == "approved" else "",
        })

    return JsonResponse({
        "ok": True,
        "is_doctor": _is_doctor(request.user),
        "calls": items,
    })


@login_required(login_url="login")
def call_room(request, call_id: int):
    call = get_object_or_404(CallRequest, pk=call_id)

    if request.user.id not in (call.user_id, call.doctor_id):
        return HttpResponseBadRequest("not allowed")

    if call.status != "approved":
        messages.error(request, "La llamada todavía no está aprobada.")
        return redirect("portal_calls")

    ctx = {
        "notifications_count": _notifications_count(request.user),
        "call": call,
        "room_key": f"call-{call.id}",
        "is_doctor": _is_doctor(request.user),
    }
    return render(request, "portal/call_room.html", ctx)


@login_required(login_url="login")
def call_signals_pull(request, room_key: str):
    try:
        after_id = int(request.GET.get("after", "0"))
    except ValueError:
        after_id = 0

    qs = CallSignal.objects.filter(room_key=room_key).order_by("id")
    if after_id:
        qs = qs.filter(id__gt=after_id)

    signals = [{"id": s.id, "sender_id": s.sender_id, "payload": s.payload} for s in qs[:200]]
    return JsonResponse({"signals": signals})


@login_required(login_url="login")
@require_POST
def call_signals_push(request, room_key: str):
    import json

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("bad json")

    CallSignal.objects.create(room_key=room_key, sender=request.user, payload=payload)
    return JsonResponse({"ok": True})


@login_required(login_url="login")
@require_POST
def appointment_create(request):
    if _is_doctor(request.user):
        return HttpResponseBadRequest("only patient")

    form = AppointmentCreateForm(request.POST)
    form.fields["doctor"].queryset = User.objects.filter(doctor_profile__activo=True)

    if not form.is_valid():
        messages.error(request, "Revisa los datos de la cita.")
        return redirect("portal_calendar_patient")

    appt: Appointment = form.save(commit=False)
    appt.patient = request.user

    if appt.end_at <= appt.start_at:
        messages.error(request, "La hora de fin debe ser posterior al inicio.")
        return redirect("portal_calendar_patient")

    appt.save()
    messages.success(request, "Cita solicitada. Queda pendiente de aprobación.")
    return redirect("portal_calendar_patient")


@login_required(login_url="login")
@require_POST
def appointment_update_status(request, appt_id: int, new_status: str):
    appt = get_object_or_404(Appointment, pk=appt_id)

    if not _is_doctor(request.user) or appt.doctor_id != request.user.id:
        return HttpResponseBadRequest("not allowed")

    if new_status not in ("approved", "rejected", "done"):
        return HttpResponseBadRequest("bad status")

    appt.status = new_status
    appt.save(update_fields=["status"])
    return redirect("portal_calendar_doctor")


@login_required(login_url="login")
def update_profile(request):
    if request.method != "POST":
        return redirect("portal_dashboard")

    first_name = (request.POST.get("first_name") or "").strip()
    last_name = (request.POST.get("last_name") or "").strip()

    if not first_name or not last_name:
        messages.error(request, "Nombre y apellidos son obligatorios.")
        return redirect("portal_dashboard")

    u = request.user
    u.first_name = first_name
    u.last_name = last_name
    u.save()

    messages.success(request, "Perfil actualizado.")
    return redirect("portal_dashboard")


@login_required(login_url="login")
def settings_view(request):
    is_doc = _is_doctor(request.user)

    patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)
    doctor_profile = getattr(request.user, "doctor_profile", None)

    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        parts = [p for p in full_name.split(" ") if p]
        if parts:
            request.user.first_name = parts[0]
            request.user.last_name = " ".join(parts[1:])
            request.user.save(update_fields=["first_name", "last_name"])

        pform = PatientProfileUpdateForm(request.POST, instance=patient_profile)
        dform = DoctorProfileUpdateForm(request.POST, request.FILES, instance=doctor_profile) if is_doc else None

        ok = pform.is_valid() and (dform.is_valid() if dform else True)
        if ok:
            pform.save()
            if dform:
                dform.save()
            messages.success(request, "Configuración guardada.")
            return redirect("portal_settings")

        messages.error(request, "Revisa los campos.")
    else:
        pform = PatientProfileUpdateForm(instance=patient_profile)
        dform = DoctorProfileUpdateForm(instance=doctor_profile) if is_doc else None

    ctx = {
        "notifications_count": _notifications_count(request.user),
        "is_doctor": is_doc,
        "patient_form": pform,
        "doctor_form": dform,
        "full_name": f"{request.user.first_name} {request.user.last_name}".strip(),
    }
    return render(request, "portal/settings.html", ctx)


@login_required(login_url="login")
@user_passes_test(_is_admin)
def doctor_list(request):
    doctores = DoctorProfile.objects.select_related("user").order_by("-created_at")
    ctx = {"notifications_count": _notifications_count(request.user), "doctores": doctores}
    return render(request, "portal/rh/doctor_list.html", ctx)


@login_required(login_url="login")
@user_passes_test(_is_admin)
def doctor_create(request):
    doctors_group = _ensure_group("Doctores")

    if request.method == "POST":
        form = DoctorCreateForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.create_user(
                username=email,
                email=email,
                password=form.cleaned_data["password"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
            )
            user.groups.add(doctors_group)

            DoctorProfile.objects.create(
                user=user,
                especialidad=form.cleaned_data.get("especialidad") or "",
                cedula=form.cleaned_data.get("cedula") or "",
                biografia=form.cleaned_data.get("biografia") or "",
                experiencia_anios=form.cleaned_data.get("experiencia_anios") or 0,
                foto=form.cleaned_data.get("foto"),
                activo=bool(form.cleaned_data.get("activo")),
            )

            messages.success(request, "Doctor registrado correctamente.")
            return redirect("doctor_list")
    else:
        form = DoctorCreateForm()

    ctx = {"notifications_count": _notifications_count(request.user), "form": form}
    
    return render(request, "portal/rh/doctor_create.html", ctx)
    
def crear_admin(request):
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@cap.com",
            password="Admin12345!"
        )
        return HttpResponse("Admin creado correctamente")
    return HttpResponse("El admin ya existe")
