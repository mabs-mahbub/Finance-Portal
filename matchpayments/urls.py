from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('matchpayment/overview/', views.matchpaymentsoverview,
         name="matchpaymentsoverview"),
    path('payment_dashboard/overview/',
         views.paymentDashboard, name="paymentDashboard"),
    path('players_payment/overview/',
         views.playersPayment, name="players_payments"),
    path('match_form/overview/', views.createMatch, name="create_match"),
    path('update_form/<str:pk>/', views.updateMatch, name="update_form"),
    path('delete_form/<str:pk>/', views.deleteMatch, name="delete_form"),
    path('action_button', views.action_button),
    path('Confirm_Payment/<str:pk>/',
         views.Confirm_Payment, name="Confirm_Payment"),
    path('Decline_Payment/<str:pk>/',
         views.Decline_Payment, name="Decline_Payment"),
    path('send_reminder/<str:pk>/', views.send_remainder, name="send_reminder"),
]
