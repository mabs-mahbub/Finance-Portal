import datetime
from django.db import models
from users.models import Profile
from django.db.models import F
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import datetime
# Create your models here.


class PaymentsData(models.Model):
    match = models.CharField(max_length=30)
    amount = models.DecimalField(default=0, max_digits=5, decimal_places=2)
    players = models.ManyToManyField(Profile, blank=True)
    playerspaid = models.ManyToManyField(
        Profile, related_name='paid', blank=True)
    datespent = models.DateField('Date Spent')

    def __str__(self):
        return self.match


@receiver(m2m_changed, sender=PaymentsData.players.through)
def send_email(sender, **kwargs):
    instance = kwargs.pop('instance', None)
    pk_set = kwargs.pop('pk_set', None)
    action = kwargs.pop('action', None)
    if action == "post_add":
        for p in instance.players.all():
            print(p)
            name = p.user.username
            payment = instance.amount
            subject = 'Payment for week ending: ' + str(datetime.date.today())
            message = 'Hello ' + name + ',' + '\n'
            message += 'A New Payment of £' + \
                str(payment) + ' has been added to your account. '
            message += 'Please visit the website to view all the payments and transfer the amount to the given account.'
            message += '\n' + 'Also, make sure to click confirm payment after processing the payment, which to be viewed by the Treasurer to aceept the request. '
            message += '\n' + 'Visit Website: ' + 'https://bp-hatters-portal.azurewebsites.net/'
            message += '\n' + 'Thank You'
            message += '\n' + 'BP Hatters'
            message += '\n' + '\n'
            send_mail(
                subject,
                message,
                'settings.EMAIL_HOST-USER',
                [p.user.email],
                fail_silently=False
            )


@receiver(m2m_changed, sender=PaymentsData.players.through)
def player_changed(sender, **kwargs):
    instance = kwargs.pop('instance', None)
    pk_set = kwargs.pop('pk_set', None)
    action = kwargs.pop('action', None)
    if action == "post_add":
        for p in pk_set:
            playerpayment = PlayersPaymentDetails.objects.get(player=p)
            playerpayment.matches.add(instance)
            instance.save()
    elif action == "post_remove" or "post_clear":
        for p in pk_set:
            playerpayment = PlayersPaymentDetails.objects.get(player=p)
            playerpayment.matches.remove(instance)
            instance.save()


PENDING_STATUS = 1
PAID_STATUS = 2

STATUS_CHOICES = (
    (PENDING_STATUS, 'Pending'),
    (PAID_STATUS, 'Paid')
)


class PaymentRequest(models.Model):
    player = models.ForeignKey(Profile, on_delete=models.CASCADE)
    matches = models.ManyToManyField(
        PaymentsData, related_name='request', blank=True)
    paid = models.DecimalField(default=0, max_digits=5, decimal_places=2)
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=PENDING_STATUS)

    def __int__(self):
        return self.paid


class PlayersPaymentDetails(models.Model):
    player = models.OneToOneField(Profile, on_delete=models.CASCADE)
    matches = models.ManyToManyField(PaymentsData, blank=True)
