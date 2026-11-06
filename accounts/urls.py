from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from django.views.generic import RedirectView

app_name = 'accounts'

# Customer accounts are switched off: the website has no customer login.
# Old links go to the homepage; staff sign in at /admin/.
home = RedirectView.as_view(url=reverse_lazy('services:home'), permanent=False)

urlpatterns = [
    path('login/', home, name='login'),
    path('register/', home, name='register'),
    path('my-account/', home, name='my_account'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
