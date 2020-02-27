from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


_MANAGED = getattr(settings, 'MONDEIQUE_MODEL_MANAGED', False)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        This method is for abstracting user model.
        NEVER CREATE USER WITH THIS SERVER!
        """
        raise Exception

    def create_superuser(self, email, password):
        """
        This method is for abstracting user model.
        NEVER CREATE USER WITH THIS SERVER!
        """
        raise Exception

    def get_queryset(self, *args, **kwargs):
        qs = super(UserManager, self).get_queryset(*args, **kwargs)
        return qs


class User(AbstractBaseUser, PermissionsMixin):
    username = None
    email = models.EmailField(verbose_name='email address', db_index=True, unique=True, null=True)
    nickname = models.CharField(max_length=30, unique=True, null=True, verbose_name='nickname')
    phone = models.CharField(max_length=19, unique=True, null=True, help_text='숫자만 입력해주세요')
    USERNAME_FIELD = 'email'

    objects = UserManager()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    quit_at = models.DateTimeField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        if _MANAGED:
            super(User, self).save(*args, **kwargs)

    def get_short_name(self):
        return self.__unicode__()

    def __unicode__(self):
        return 'user{}'.format(self.id)

    def __str__(self):
        if self.is_anonymous:
            return 'anonymous'
        if self.nickname:
            return self.nickname
        if self.email:
            return self.email
        return self.phone

    class Meta:
        db_table = 'accounts_user'
        managed = _MANAGED


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    thumbnail_img = models.ImageField(default='default_profile.png', null=True, blank=True)
    introduce = models.TextField(verbose_name='소개', default="")

    @property
    def thumbnail_img_url(self):
        """
            1. thumbnail_img가 자신이 올린 것이 있을 경우
            2. 없으면 socialaccount의 last의 img사용
            3. 없을시 default사용
            """
        if self.thumbnail_img.name != "default_profile.png":
            return self.thumbnail_img.url
        elif hasattr(self.user.socialaccount_set.last(), 'extra_data'):
            if 'properties' in self.user.socialaccount_set.last().extra_data:
                return self.user.socialaccount_set.last().extra_data['properties'].get('thumbnail')
        else:
            return self.thumbnail_img.url

    class Meta:
        db_table = 'accounts_profile'
        managed = _MANAGED

