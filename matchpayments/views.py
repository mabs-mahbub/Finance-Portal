from difflib import Match
from multiprocessing import context
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import PaymentsData, PaymentRequest, PlayersPaymentDetails
from users.models import Profile
from django.http import HttpResponse
from django.shortcuts import redirect
from .forms import MatchForm
import datetime
from django.core.mail import send_mail
from .decorators import allowed_users, admin_only
from django.db.models.signals import post_save
from django.conf import settings
# Create your views here.


def action_button(request):
    if request.method == 'POST':
        user = request.user
        user_profile = Profile.objects.get(user=user.id)
        matches = PaymentsData.objects.filter(players=user_profile.id)

        # pre-populating a instant as we need to insert matches into many to many field after creating and saving instant
        pr = PaymentRequest(player=user_profile)
        pr.save()

        # below code we are adding all the matches that has been send to request and are pending
        requestedPayments = PaymentRequest.objects.filter(
            player=user_profile, status=1)
        pending = []
        for rp in requestedPayments:
            val = rp.matches.values()
            for item in val:
                pending.append(item['id'])

        # if they are not on pending we add matches to the request above and the total amount
        for m in matches:
            if m.id not in pending:
                pr.paid += m.amount
                pr.save()
                pr.matches.add(m)

        # if they are not we just delete the instance we created at start to avoid duplication
        checkifexist = PaymentRequest.objects.get(id=pr.id).matches.values()
        if not checkifexist:
            PaymentRequest.objects.get(id=pr.id).delete()

    return redirect('/matchpayment/overview')


@login_required
@allowed_users(allowed_roles=['Treasurer'])
def paymentDashboard(request):
    totalMatches = PaymentsData.objects.count()
    totalRequest = PaymentRequest.objects.count()
    matchDetails = PaymentsData.objects.all()
    requestDetails = PaymentRequest.objects.all()
    return render(request, 'matchpayments/Payment_Dashboard.html', context={'totalMatches': totalMatches,
                                                                            'totalRequest': totalRequest, 'matches': matchDetails, 'requests': requestDetails})


@login_required
@allowed_users(allowed_roles=['Treasurer'])
def playersPayment(request):
    playersPaymentDetails = PlayersPaymentDetails.objects.all()
    dueMatches = 0
    dueTotal = 0
    players_data = []
    matches = {}
    for pp in playersPaymentDetails:
        amountdue = 0

        nomatches = pp.matches.count()
        dueMatches += pp.matches.count()
        for i in pp.matches.all():
            amountdue += i.amount
            dueTotal += i.amount
            #print(dueTotal)
        
        players_data.append({
            "id" : pp.id,
            "name": pp.player.user.username,
            "nomatches": nomatches,
            "totalamount": amountdue,
            "matches": pp.matches.all()
        })

    return render(request, 'matchpayments/playersPayment.html', context={'playerpayments': playersPaymentDetails, 'dueMatches': dueMatches, 'players_data' : players_data, 'dueTotal': dueTotal})

# loads when the payment forms load


@login_required
def matchpaymentsoverview(request):

    user = request.user
    user_profile = Profile.objects.get(user=user.id)

    requestedPayments = PaymentRequest.objects.filter(
        player=user_profile, status=1)
    # here we are gathering all the payment that has been requested already to pending variable
    # which will be passed to html file to change the status by checking if the user already made request
    pending = []
    for rp in requestedPayments:
        val = rp.matches.values()
        for item in val:
            pending.append(item['id'])

    # this will calculate the amount to be paid
    matches = PaymentsData.objects.filter(players=user_profile.id)
    total = 0
    for m in matches:
        # below if statement checks if the match is on pending if it is, it does not count the amount
        # it only counts the pay status
        if m.id not in pending:
            total += m.amount

    # below code to count only the paid matches total
    paidmatches = PaymentsData.objects.filter(playerspaid=user_profile.id)
    totalpaid = 0
    for p in paidmatches:
        totalpaid += p.amount

    return render(request, 'matchpayments/matchpayments.html',
                  context={'matches': matches, 'pending': pending, 'total': total, 'paidmatches': paidmatches, 'totalpaid': totalpaid})


@login_required
@allowed_users(allowed_roles=['Treasurer'])
def createMatch(request):
    form = MatchForm()
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            form.save()
            form.save()
            return redirect('/payment_dashboard/overview/')
    context = {'form': form}
    return render(request, 'matchpayments/create_match.html', context)


@login_required
@allowed_users(allowed_roles=['Treasurer'])
def updateMatch(request, pk):
    match = PaymentsData.objects.get(id=pk)
    form = MatchForm(instance=match)

    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            return redirect('/payment_dashboard/overview/')
    context = {'form': form}
    return render(request, 'matchpayments/create_match.html', context)


@login_required
@allowed_users(allowed_roles=['Treasurer'])
def deleteMatch(request, pk):
    match = PaymentsData.objects.get(id=pk)

    if request.method == 'POST':
        match.delete()
        return redirect('/payment_dashboard/overview/')
    context = {'item': match}
    return render(request, 'matchpayments/delete.html', context)


@login_required
@allowed_users(allowed_roles=['Treasurer'])
def Confirm_Payment(request, pk):
    req = PaymentRequest.objects.get(id=pk)
    user_profile = Profile.objects.get(user=req.player.id)
    matches = PaymentsData.objects.filter(players=user_profile.id)
    if request.method == "POST":
        for m in matches:
            m.players.remove(user_profile)
            m.playerspaid.add(user_profile)
            m.save()
        req.delete()
        return redirect('/payment_dashboard/overview/')
    context = {'item': req}
    return render(request, 'matchpayments/paymentConfirm.html', context)


@login_required
@allowed_users(allowed_roles=['Treasurer'])
def Decline_Payment(request, pk):
    req = PaymentRequest.objects.get(id=pk)
    if request.method == "POST":
        req.delete()
        return redirect('/payment_dashboard/overview/')
    context = {'item': req}
    return render(request, 'matchpayments/paymentDecline.html', context)


@login_required
@allowed_users(allowed_roles=['Treasurer'])
def send_remainder(request, pk):
    pp = PlayersPaymentDetails.objects.get(id=pk)
    if request.method == "POST":
        name = pp.player.user.username
        matches = pp.matches.all()
        
        # Initialize total amount to 0
        total_amount_due = 0
        
        # Loop through each match and add up the amounts
        for match in matches:
            total_amount_due += match.amount

        subject = 'Payment reminder for week ending: ' + \
            str(datetime.date.today())
        message = 'Hello ' + name + ',' + '\n'
        message += 'This is a reminder for your payment thats due, where you have total of £' + \
            str(total_amount_due) + ' to be paid. '
        message += 'Please visit the website to view all the payments and transfer the amount to the given account.'
        message += '\n' + 'Also, make sure to click confirm payment after processing the payment, which to be viewed by the Treasurer to aceept the request. '
        message += '\n' + 'Visit Website: ' + 'https://bp-hatters-portal.azurewebsites.net/matchpayment/overview/'
        message += '\n' + 'Thank You'
        message += '\n' + 'BP Hatters'
        message += '\n' + '\n'
        send_mail(
            subject,
            message,
            'settings.EMAIL_HOST-USER',
            [pp.player.user.email],
            fail_silently=False
        )
        return redirect('/payment_dashboard/overview/')
    context = {'item': pp}
    return render(request, 'matchpayments/confirm_mail.html', context)
