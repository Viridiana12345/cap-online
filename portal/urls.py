from django.urls import path
from . import views

urlpatterns = [

    path("", views.landing, name="landing"),

    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", views.signup, name="signup"),

    # Portal
    path("portal/", views.dashboard, name="portal_dashboard"),
    path("portal/notificaciones/", views.notifications, name="portal_notifications"),
    path("portal/chat/", views.chat, name="portal_chat"),
    path("portal/chat/<int:user_id>/", views.chat, name="portal_chat_with"),
    path("portal/especialistas/", views.specialists, name="portal_specialists"),
    path("portal/calendario/", views.calendar_view, name="portal_calendar"),
    path("portal/calendario/paciente/", views.calendar_patient, name="portal_calendar_patient"),
    path("portal/calendario/doctor/", views.calendar_doctor, name="portal_calendar_doctor"),
    path("portal/llamadas/", views.calls, name="portal_calls"),
    path("portal/perfil/<int:doctor_id>/", views.profile, name="portal_profile"),
    path("portal/configuracion/", views.settings_view, name="portal_settings"),

    # RH
    path("portal/rh/doctores/nuevo/", views.doctor_create, name="doctor_create"),
    path("portal/rh/doctores/", views.doctor_list, name="doctor_list"),

    # CHAT
    path("portal/send-message/<int:user_id>/", views.send_message, name="send_message"),
    path("portal/api/chat/thread/<int:user_id>/", views.chat_thread_api, name="chat_thread_api"),
    path("portal/api/chat/send/<int:user_id>/", views.chat_send_api, name="chat_send_api"),

    # LLAMADAS
    path("portal/request-call/", views.request_call, name="request_call"),
    path("portal/call/<int:call_id>/room/", views.call_room, name="call_room"),
    path("portal/call/<int:call_id>/status/<str:new_status>/", views.call_update_status, name="call_update_status"),

    # API llamadas (señalización WebRTC)
    path("portal/api/call/<str:room_key>/pull/", views.call_signals_pull, name="call_signals_pull"),
    path("portal/api/call/<str:room_key>/push/", views.call_signals_push, name="call_signals_push"),

    # NUEVA API para actualizar llamadas
    path("portal/api/calls/status/", views.call_status_api, name="call_status_api"),

    # PERFIL
    path("portal/update-profile/", views.update_profile, name="update_profile"),

    # CITAS
    path("portal/appointment/create/", views.appointment_create, name="appointment_create"),
    path("portal/appointment/<int:appt_id>/status/<str:new_status>/", views.appointment_update_status, name="appointment_update_status"),
]