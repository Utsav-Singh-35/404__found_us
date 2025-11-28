from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from .mongodb import mongodb
from bson import ObjectId
from django.contrib.auth.hashers import make_password, check_password as django_check_password


class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        # Save to MongoDB if available
        if mongodb.is_connected():
            try:
                user_data = {
                    'email': email,
                    'name': name,
                    'password': make_password(password),
                    'is_active': extra_fields.get('is_active', True),
                    'is_staff': extra_fields.get('is_staff', False),
                    'is_superuser': extra_fields.get('is_superuser', False),
                    'date_joined': timezone.now()
                }
                result = mongodb.users.insert_one(user_data)
                user_data['_id'] = result.inserted_id
                print(f"✅ User saved to MongoDB: {email}")
            except Exception as e:
                print(f"⚠️  MongoDB save failed: {e}")
        
        # Also save to Django DB for admin
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, name, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    # Alert Preferences
    email_alerts = models.BooleanField(default=True)
    sms_alerts = models.BooleanField(default=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.name
    
    def get_short_name(self):
        return self.name
