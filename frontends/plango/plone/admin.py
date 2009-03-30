from django.contrib import admin
from plone.models.base import Content, Document, Image, LargeFolder, Link, NewsItem, Folder, File, Event, Favorite

class ContentAdmin( admin.ModelAdmin ):
    list_display = ('content_id', 'portal_type', 'title','status', 'creators', 'modification_date', 'id')
    list_filter = ('type', 'status')
    _properties = {
        'classes': ('collapse',),
        'fields': ('subject', 'location', 'contributors', 'creators', 'language', 'rights'),
    }
    _dates = {
        'classes': ('collapse',),
        'fields': ('creation_date', 'modification_date', 'effectivedate', 'expirationdate'),
    }
    fieldsets = (
        (None, {'fields': ("title", "description")}),
        ('Properties', _properties),
        ('Dates', _dates),
    )    
    date_hierarchy = 'modification_date'

admin.site.register( Content, ContentAdmin )

class DocumentAdmin(ContentAdmin):
    fieldsets = (
            (None, {'fields': ("title", "description", "text")}),
            ('Properties', ContentAdmin._properties),
            ('Dates', ContentAdmin._dates)
        )    
        
admin.site.register(Document, DocumentAdmin)

admin.site.register(Image, ContentAdmin)

admin.site.register(LargeFolder, ContentAdmin)

class LinkAdmin(ContentAdmin):
    fieldsets = (
            (None, {'fields': ("title", "description", "remoteurl")}),
            ('Properties', ContentAdmin._properties),
            ('Dates', ContentAdmin._dates)
        )
        
admin.site.register( Link, LinkAdmin )

class NewsItemAdmin(ContentAdmin):
    fieldsets = (
            (None, {'fields': ("title", "description", "text", "imagecaption")}),
            ('Properties', ContentAdmin._properties),
            ('Dates', ContentAdmin._dates)
        )

admin.site.register( NewsItem, NewsItemAdmin)

admin.site.register( Folder, ContentAdmin )

admin.site.register( File, ContentAdmin )

class EventAdmin(ContentAdmin):
    fieldsets = (
            (None, {'fields': ("title", "description", "startdate", "enddate", "text", "attendees", "eventtype", "eventurl", "contactname", "contactemail", "contactphone")}),
            ('Properties', ContentAdmin._properties),
            ('Dates', ContentAdmin._dates)
        )

admin.site.register( Event, EventAdmin )

class FavoriteAdmin(ContentAdmin):
    fieldsets = (
            (None, {'fields': ("title", "description", "remoteurl")}),
            ('Properties', ContentAdmin._properties),
            ('Dates', ContentAdmin._dates)
        )
                
admin.site.register( Favorite, FavoriteAdmin )