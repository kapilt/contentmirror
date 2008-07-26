from django.db import models
from django.contrib import admin

class Content(models.Model):
    class Meta:
        db_table = u'content'
            
    content_id = models.IntegerField(primary_key=True)
    id = models.CharField(max_length=256)
    uid = models.CharField(unique=True, max_length=36)
    portal_type = models.CharField(max_length=64)
    status = models.CharField(max_length=64)
    type = models.CharField(max_length=64)
    container = models.ForeignKey('self')
    title = models.TextField()
    description = models.TextField()
    subject = models.TextField()
    location = models.TextField()
    contributors = models.TextField()
    creators = models.TextField()
    creation_date = models.DateTimeField()
    modification_date = models.DateTimeField()
    effectivedate = models.DateTimeField()
    expirationdate = models.DateTimeField()
    language = models.TextField()
    rights = models.TextField()


    def __unicode__( self ):
        return self.type + self.id + self.title

class ContentAdmin( admin.ModelAdmin ):
    list_display = ('portal_type', 'title','status', 'creators', 'modification_date', 'id')
    list_filter = ('type', 'status')    
    #date_hierarchy = 'modification_date'

admin.site.register( Content, ContentAdmin )
        
class Relations(models.Model):
    source = models.ForeignKey(Content, related_name="refs")
    target = models.ForeignKey(Content, related_name="backrefs")
    relationship = models.CharField(max_length=128)
    
    class Meta:
        db_table = u'relations'

class Files(models.Model):
    content = models.ForeignKey(Content)
    attribute = models.CharField(max_length=156)
    type = models.CharField(max_length=30)
    content = models.TextField() # This field type is a guess.
    path = models.CharField(max_length=300)
    size = models.IntegerField()
    checksum = models.CharField(max_length=33)
    file_name = models.CharField(max_length=156)
    mime_type = models.CharField(max_length=80)
    class Meta:
        db_table = u'files'

######################################
# Content Types

class Document(models.Model):
    content = models.ForeignKey(Content)
    text = models.TextField()
    class Meta:
        db_table = u'atdocument'

admin.site.register( Document )

class Image(models.Model):
    content = models.ForeignKey(Content)
    class Meta:
        db_table = u'atimage'

#admin.site.register( Image )

class LargeFolder(models.Model):
    content_id = models.IntegerField(primary_key=True)    
    content = models.ForeignKey(Content)
    constraintypesmode = models.IntegerField()
    locallyallowedtypes = models.TextField()
    immediatelyaddabletypes = models.TextField()
    class Meta:
        db_table = u'atbtreefolder'

admin.site.register( LargeFolder )

class Link(models.Model):
    content = models.ForeignKey(Content)
    remoteurl = models.TextField()
    class Meta:
        db_table = u'atlink'

#admin.site.register( Link )

class NewsItem(models.Model):
    content_id = models.IntegerField(primary_key=True)            
    content = models.ForeignKey(Content)
    text = models.TextField()
    imagecaption = models.TextField()
    class Meta:
        db_table = u'atnewsitem'

admin.site.register( NewsItem )

class Folder(models.Model):
    content_id = models.IntegerField(primary_key=True)        
    content = models.ForeignKey(Content)
    constraintypesmode = models.IntegerField()
    locallyallowedtypes = models.TextField()
    immediatelyaddabletypes = models.TextField()
    class Meta:
        db_table = u'atfolder'

admin.site.register( Folder )

class File(models.Model):
    content = models.ForeignKey(Content)
    class Meta:
        db_table = u'atfile'

#admin.site.register( File )

class Event(models.Model):
    content = models.ForeignKey(Content)
    startdate = models.DateTimeField()
    enddate = models.DateTimeField()
    text = models.TextField()
    attendees = models.TextField()
    eventtype = models.TextField()
    eventurl = models.TextField()
    contactname = models.TextField()
    contactemail = models.TextField()
    contactphone = models.TextField()
    class Meta:
        db_table = u'atevent'

admin.site.register( Event )        

class Favorite(models.Model):
    content = models.ForeignKey(Content)
    remoteurl = models.TextField()
    class Meta:
        db_table = u'atfavorite'

admin.site.register( Favorite )        



