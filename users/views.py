from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import EditProfileForm, LoginForm, SignUpForm
from .models import Profile, User


def signup(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('core:home')
    else:
        form = SignUpForm()

    return render(request, 'users/signup.html', {'form': form})


def log_in(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(
                    next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
                ):
                    return redirect(next_url)
                return redirect('core:home')
            form.add_error(None, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


def log_out(request):
    logout(request)
    return redirect('users:login')


@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(Profile, user=user)
    return render(request, 'users/profile.html', {'user': user, 'profile': profile})


@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = EditProfileForm(
            request.POST, request.FILES, original_username=request.user.username
        )
        if form.is_valid():
            request.user.username = form.cleaned_data['username']
            request.user.save()

            profile.about_me = form.cleaned_data['about_me']
            if form.cleaned_data.get('image'):
                profile.image = form.cleaned_data['image']
            profile.save()

            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('users:profile', username=request.user.username)
    else:
        form = EditProfileForm(
            initial={'username': request.user.username, 'about_me': profile.about_me},
            original_username=request.user.username,
        )

    return render(request, 'users/edit_profile.html', {'form': form})
