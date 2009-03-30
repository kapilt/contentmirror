from plone.models.base import Document, Content, Folder

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.views.static import was_modified_since
from django.utils.http import http_date

from plone.utils import paginate
from plone.models.search import Search

from time import mktime

def front_page(request):
    document = Document.objects.get(id="front-page", container=None, status="published")
    context = { "object": document, "sub_objects": Folder.objects.filter(container=None, status="published"), }
    return render_to_response('index.html', context, 
        context_instance=RequestContext(request)
        )

def images(request, id):
    content = Content.objects.get(content_id=id)
    file = content.files_to_content.get()
    data = file.content
        
    response = HttpResponse(data, mimetype=file.mime_type)
    response["Last-Modified"] = http_date(mktime(content.modification_date.timetuple()))
    response["Content-Length"] = len(data)
    return response

def search(request):
    query = request.GET.get("q")

    if query:
        results = Search.query(query)
    else:
        results = []

    paginator, page, number = paginate(results, request)

    return render_to_response('search.html', {
            "results": results,
            "paginator": page,
            "query": query
             },
        context_instance=RequestContext(request)
        )