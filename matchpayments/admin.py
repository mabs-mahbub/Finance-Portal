from django.contrib import admin
from .models import PaymentsData,PaymentRequest, Profile, PlayersPaymentDetails
from import_export.admin import ImportExportModelAdmin

admin.site.site_header = "BP Admin Management"
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('player', 'paid' ,'status')
    list_filter = ('status',)

    model = PaymentRequest
    actions = ['Confirm_Payment']

    #each time use selects and clicks the button 
    #it will go through all the matches within the selected request and change from players - players paid
    def Confirm_Payment(self, request, queryset):
        user = request.user
        user_profile = Profile.objects.get(user = user.id)
        matches = PaymentsData.objects.filter(players = user_profile.id)
        for m in matches:
            m.players.remove(user_profile)
            m.playerspaid.add(user_profile)
            
        
admin.site.register(PaymentRequest, PaymentRequestAdmin)

class PaymentsDataAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('match', 'datespent')

admin.site.register(PaymentsData, PaymentsDataAdmin)

class PlayersPaymentAdmin(admin.ModelAdmin):
    list_display = ('player',)

admin.site.register(PlayersPaymentDetails, PlayersPaymentAdmin)