from django.contrib import admin
from .models import Card, CardReview, Topic

admin.site.register(Topic)
admin.site.register(Card)
admin.site.register(CardReview)
