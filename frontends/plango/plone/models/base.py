from django.db import models
from django.contrib.contenttypes.models import ContentType

from plone.utils import normalize_name

class Content(models.Model):
    class Meta:
        db_table = u'content'
        app_label = 'plone'
                    
    content_id = models.IntegerField(primary_key=True, editable=False)
    id = models.CharField(max_length=256, editable=False)
    uid = models.CharField(unique=True, max_length=36, editable=False)
    portal_type = models.CharField(max_length=64, editable=False)
    status = models.CharField(max_length=64, editable=False, null=False)
    type = models.CharField(max_length=64, editable=False)
    container = models.ForeignKey('self', related_name="parent", editable=False)
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
    
    def get_search_fields(self):
        return [self.title, self.description, self.subject]
    
    def normalize_name(self):
        return normalize_name(self.type)

    def verbose_name(self):
        return self.normalize_name()

    def get_nice_creation_date(self):
        return self.creation_date.strftime("%b, %d")

    def get_nice_modified_date(self):
        return self.modification_date.strftime("%b, %d")
            
    def content_object(self):
        content_type = ContentType.objects.get(app_label="plone", model=normalize_name(self.type))
        klass = content_type.model_class()
        return klass.objects.get(content_id=self.content_id)

    def default_template_name(self):
        return self.normalize_name() + ".html"

    def default_context(self):
        result = {}
        sub_objects = Content.objects.filter(container=self, status="published").order_by("title")
        if sub_objects:
            result["sub_objects"] = sub_objects
        return result

    def get_absolute_url(self):
        current = self
        url = []

        # assuming nothing is going to be more than 40 deep
        for x in range(0, 40):
            try:
                if current.container:
                    url.append(current.id)
                    current = current.container 
                else:
                    break
            # should be doing current.DoesNotExist
            except:
                break

        url.append(current.id)
        url.reverse()
        return "/" + "/".join(url)

    def __unicode__( self ):
        return self.type + self.id + self.title
        
class Relations(models.Model):
    source = models.ForeignKey(Content, related_name="refs")
    target = models.ForeignKey(Content, related_name="backrefs")
    relationship = models.CharField(max_length=128)
    
    class Meta:
        db_table = u'relations'
        app_label = 'plone'

class Files(models.Model):
    content_id = models.ForeignKey(Content, primary_key=True, db_column="content_id", related_name="files_to_content")
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
        app_label = 'plone'

######################################
# Content Types
    

class Document(Content):
    content = models.OneToOneField(Content, parent_link=True, related_name="documents")
    text = models.TextField()
    
    def get_search_fields(self):
        base = super(Document,self).get_search_fields()
        base.append(self.text)
        return base
    
    class Meta:
        db_table = u'atdocument'
        app_label = 'plone'

class Image(Content):
    content = models.OneToOneField(Content, parent_link=True, related_name="images")
    
    def get_download_url(self):
        return "/images/%s/" % (self.content_id)
    
    
    class Meta:
        db_table = u'atimage'
        app_label = 'plone'

class LargeFolder(Content):   
    content = models.OneToOneField(Content, parent_link=True, related_name="largefolders")
    constraintypesmode = models.IntegerField()
    locallyallowedtypes = models.TextField()
    immediatelyaddabletypes = models.TextField()
    
    class Meta:
        db_table = u'atbtreefolder'

class Link(Content):
    content = models.OneToOneField(Content, parent_link=True, related_name="links")
    remoteurl = models.TextField()
    
    class Meta:
        db_table = u'atlink'
        app_label = 'plone'

class NewsItem(Content):         
    content = models.OneToOneField(Content, parent_link=True, related_name="newsitems")
    text = models.TextField()
    imagecaption = models.TextField()
    
    def get_search_fields(self):
        base = super(NewsItem,self).get_search_fields()
        base.append(self.text)
        base.append(self.imagecaption)
        return base
    
    class Meta:
        db_table = u'atnewsitem'
        app_label = 'plone'

class Folder(Content):   
    content = models.OneToOneField(Content, parent_link=True, related_name="folders")
    constraintypesmode = models.IntegerField()
    locallyallowedtypes = models.TextField()
    immediatelyaddabletypes = models.TextField()
    
    class Meta:
        db_table = u'atfolder'
        app_label = 'plone'

class File(Content):
    content = models.OneToOneField(Content, parent_link=True, related_name="files")
    
    class Meta:
        db_table = u'atfile'
        app_label = 'plone'

class Event(Content):
    content = models.OneToOneField(Content, parent_link=True, related_name="events")
    startdate = models.DateTimeField()
    enddate = models.DateTimeField()
    text = models.TextField()
    attendees = models.TextField()
    eventtype = models.TextField()
    eventurl = models.TextField()
    contactname = models.TextField()
    contactemail = models.TextField()
    contactphone = models.TextField()
    
    def get_search_fields(self):
        base = super(Event,self).get_search_fields()
        base.append(self.text)
        return base
        
    class Meta:
        db_table = u'atevent'
        app_label = 'plone'

class Favorite(Content):
    content = models.OneToOneField(Content, parent_link=True, related_name="favorites")
    remoteurl = models.TextField()
    
    class Meta:
        db_table = u'atfavorite'
        app_label = 'plone'        