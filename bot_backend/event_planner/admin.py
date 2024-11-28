from django.contrib import admin
from .models import Event, Speaker, Session, SpeakerSession


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'location')
    search_fields = ('name', 'location')
    list_filter = ('date',)
    ordering = ('date',)


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    list_display = ('name', 'stack')
    search_fields = ('name', 'stack')
    ordering = ('name',)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'event')
    search_fields = ('title', 'event__name')
    list_filter = ('event',)
    ordering = ('event__date',)


@admin.register(SpeakerSession)
class SpeakerSessionAdmin(admin.ModelAdmin):
    list_display = ('speaker', 'topic', )
    search_fields = ('speaker__name', 'topic')
    ordering = ('session__event__date',)
