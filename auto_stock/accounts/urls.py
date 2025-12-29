from django.urls import path
from accounts import views

urlpatterns = [
    # 회원가입 
    path('signup/', views.SignupView.as_view(), name='signup'),
    # 로그인 
    path('login/', views.LoginView.as_view(), name='login'),
    # 로그아웃
    path('logout/', views.LogoutView.as_view(), name='logout'),
    # 회원 탈퇴 
    path('delete/', views.DeleteAccountView.as_view(), name='delete'),
]