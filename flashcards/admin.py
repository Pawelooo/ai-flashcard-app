from django.contrib import admin
from .models import Card, CardReview, TimedRun, Topic

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'slug')
    list_display_links = ('name',)
    fields = ('name', 'slug', 'icon', 'description')
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Card)
admin.site.register(CardReview)


@admin.register(TimedRun)
class TimedRunAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'score', 'answered', 'started_at', 'finished_at')
    list_filter = ('topic',)
    ordering = ('-score',)
