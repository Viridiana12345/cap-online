INSTRUCCIONES RAPIDAS

1) Activar entorno virtual (opcional si ya lo tienes)
2) Ejecutar:
   python manage.py migrate
   python manage.py runserver

3) Registrar psicologos desde RH:
   /portal/rh/doctores/nuevo/

IMPORTANTE:
- El login usa correo como username.
- Para doctores creados en RH, el sistema guarda username=email automaticamente.
- Si quieres entrar al admin, crea un superusuario con:
  python manage.py createsuperuser
