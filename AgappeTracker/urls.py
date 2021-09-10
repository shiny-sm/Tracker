from django.contrib import admin
from django.urls import include, path
from tracker import views
urlpatterns = [
    path('tracker/', include('tracker.urls')),
    path('admin/', admin.site.urls),
    path('forgotpwd/', views.forgotpassword),
    path('registration/', views.registration),
    path('',views.logins, name='loginpage'),
    path('logout/',views.logouts),
]