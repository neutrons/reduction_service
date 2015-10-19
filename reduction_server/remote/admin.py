from models import Transaction
from django.contrib import admin

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'trans_id', 'directory', 'owner', 'start_time')
    
admin.site.register(Transaction, TransactionAdmin)
