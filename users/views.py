from django.shortcuts import render, redirect
from .forms import ProfileForm, CustomUserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from .models import UserProfile
from django.contrib.auth import login
from django.contrib import messages
from orders.models import Order
from django.contrib.auth import logout
from django.shortcuts import redirect



class ProfileView(LoginRequiredMixin, View):
    template_name = 'users/profile.html'
    login_url = 'login'

    def get_profile(self, request):
        profile, created = UserProfile.objects.get_or_create(
            user = request.user
        )
        return profile

    def get(self, request):
        profile = self.get_profile(request)

        form = ProfileForm(instance=profile)

        orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')

        return render(
            request,
            self.template_name,
            {
                'form': form,
                'profile': profile,
                'orders': orders
            }
        )

    def post(self, request):
        profile = self.get_profile(request)

        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():
            form.save()
            return redirect('users:profile')

        return render(
            request,
            self.template_name,
            {
                'form' : form,
                'profile' : profile
            }
        )

class RegisterView(View):
    template_name = 'users/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('user:profile')

        form = CustomUserCreationForm()

        return render(request, self.template_name, {'form' : form})

    def post(self, request):
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            UserProfile.objects.get_or_create(user = user)

            login(request, user, backend = 'django.contrib.auth,backends.ModelBackend')

            messages.success(
                self.request,
                'Ви успішно зареєструвались'
            )

            return redirect('users:profile')

        return render(request, self.template_name, {'form' : form, 'message' : messages})

def logout_view(request):
    logout(request)
    return redirect('store:home')





