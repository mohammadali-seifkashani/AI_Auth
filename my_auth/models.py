from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.base_user import BaseUserManager


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class MyUser(AbstractBaseUser):
    email = models.EmailField(_('email address'), unique=True)
    revealing_password = models.CharField(max_length=6)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email
#
#
# class UserImage(models.Model):
#     user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
#     image = models.FileField(upload_to='images/')
#
#
# class UserVoice(models.Model):
#     user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
#     voice = models.FileField(upload_to='voices/')

