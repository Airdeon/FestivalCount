import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_can_create_and_authenticate_user():
    user = User.objects.create_user(username="testuser", password="pass12345")
    assert user.pk is not None
    assert user.check_password("pass12345") is True
