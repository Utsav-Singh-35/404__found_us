from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
from .mongodb import mongodb
from django.contrib.auth.hashers import make_password, check_password


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Validation
        if not all([name, email, password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'auth/signup.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'auth/signup.html')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'auth/signup.html')
        
        try:
            user = CustomUser.objects.create_user(
                email=email,
                name=name,
                password=password
            )
            login(request, user)
            messages.success(request, f'Welcome to SatyaMatrix, {name}! Your account has been created successfully.')
            return redirect('chat')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'auth/signup.html')
    
    return render(request, 'auth/signup.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not all([email, password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'auth/login.html')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.name}!')
            next_url = request.GET.get('next', 'chat')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'auth/login.html')
    
    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def profile_view(request):
    if request.method == 'POST':
        # Update alert preferences
        email_alerts = request.POST.get('email_alerts') == 'on'
        sms_alerts = request.POST.get('sms_alerts') == 'on'
        
        user = request.user
        user.email_alerts = email_alerts
        user.sms_alerts = sms_alerts
        user.save()
        
        # Also update in MongoDB if connected
        if mongodb.is_connected():
            try:
                mongodb.users.update_one(
                    {'email': user.email},
                    {'$set': {
                        'email_alerts': email_alerts,
                        'sms_alerts': sms_alerts
                    }}
                )
            except Exception as e:
                print(f"MongoDB update error: {e}")
        
        messages.success(request, 'Alert preferences updated successfully!')
        return redirect('profile')
    
    return render(request, 'auth/profile.html', {'user': request.user})


@login_required
def chat_view(request):
    return render(request, 'dashboards/chat.html', {'user': request.user})


def home_view(request):
    return render(request, 'index.html')


@login_required
def trending_view(request):
    return render(request, 'dashboards/trending.html', {'user': request.user})
