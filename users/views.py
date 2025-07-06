#from email.headerregistry import Group
from os import name
from tokenize import group
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import Group, User
from matchpayments.models import PlayersPaymentDetails
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            group = Group.objects.get(name='Players')
            user.groups.add(group)
            messages.success(request,'Account has been created for ' + username + " You are now able to log in")
            print(user)

            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@receiver(post_save, sender=Profile)
def create_profile(sender, instance, created, **kwargs):
    if created:
        PlayersPaymentDetails.objects.create(player=instance)


@receiver(post_save, sender=Profile)
def save_profile(sender, instance, **kwargs):
    instance.playerspaymentdetails.save()

def loginPage(request):
    if request.method == 'POST':
        if request.POST.get('username') != '':
            username = request.POST.get('username')
            password =request.POST.get('password')

            user = authenticate(request, username=username, password=password)
        
            group = None

            if request.user.groups.exists():
                group = request.user.groups.all()[0].name
	    
            if user is not None and group == 'Treasurer':
                login(request, user)
                return redirect('paymentDashboard')
            elif user is not None:
                login(request, user)
                return redirect('matchpaymentsoverview')
            else:
                messages.info(request, 'Username OR password is incorrect')
        else:
            messages.info(request, 'Please fill the required username field')

    context = {}
    return render(request, 'users/login.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'users/profile.html', context)
