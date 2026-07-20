from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail import send_mail
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.email = "testuser@example.com"
        self.password = "OldPass123!"
        self.user = User.objects.create_user(
            username=self.email,
            email=self.email,
            password=self.password,
        )

    def test_password_reset_page_loads(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recuperar contraseña")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEBUG=False,
        RENDER_EXTERNAL_HOSTNAME="cap-online.onrender.com",
        DEFAULT_FROM_EMAIL="viridianahernandez02635@gmail.com",
    )
    def test_password_reset_email_is_sent_for_registered_user(self):
        response = self.client.post(reverse("password_reset"), {"email": self.email})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.email, mail.outbox[0].to)
        self.assertTrue(mail.outbox[0].subject.strip())
        self.assertNotIn("\n", mail.outbox[0].subject)
        self.assertIn("https://cap-online.onrender.com/reset/", mail.outbox[0].body)
        self.assertNotIn("localhost", mail.outbox[0].body)
        self.assertNotIn("127.0.0.1", mail.outbox[0].body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEBUG=False,
        RENDER_EXTERNAL_HOSTNAME="cap-online.onrender.com",
        DEFAULT_FROM_EMAIL="viridianahernandez02635@gmail.com",
    )
    def test_password_reset_link_changes_password_and_allows_login(self):
        self.client.post(reverse("password_reset"), {"email": self.email})
        self.assertEqual(len(mail.outbox), 1)

        reset_url = next(
            line.strip()
            for line in mail.outbox[0].body.splitlines()
            if line.strip().startswith("https://")
        )
        self.assertEqual(urlsplit(reset_url).netloc, "cap-online.onrender.com")
        reset_path = urlsplit(reset_url).path

        response = self.client.get(reset_path, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nueva contraseña")

        post_path = reset_path
        if response.redirect_chain:
            post_path = response.redirect_chain[-1][0]

        response = self.client.post(
            post_path,
            {
                "new_password1": "NewPass123!",
                "new_password2": "NewPass123!",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(email=self.email)
        self.assertTrue(user.check_password("NewPass123!"))

        login_response = self.client.post(
            reverse("login"),
            {"email": self.email, "password": "NewPass123!"},
        )
        self.assertRedirects(
            login_response,
            reverse("portal_dashboard"),
            fetch_redirect_response=False,
        )
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_inactive_user_does_not_receive_password_reset_email(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(reverse("password_reset"), {"email": self.email})

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_direct_send_mail_works_without_silencing_errors(self):
        sent_count = send_mail(
            "Prueba de envío",
            "Este es un correo de prueba.",
            "viridianahernandez02635@gmail.com",
            [self.email],
            fail_silently=False,
        )
        self.assertEqual(sent_count, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Prueba de envío")
        self.assertIn(self.email, mail.outbox[0].to)
