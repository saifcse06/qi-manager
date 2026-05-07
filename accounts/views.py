from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

def index_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    return redirect('login')

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'
    login_url = '/login/'

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'
    login_url = '/login/'