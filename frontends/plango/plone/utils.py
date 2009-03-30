from django.core.paginator import Paginator, EmptyPage, InvalidPage

def normalize_name(type):
    return type.lower().replace("at", "")[:-4]
    
def paginate(queryset, request):
    paginator = Paginator(queryset, 25)
    try:
        number = int(request.GET.get("page", 1))
    except ValueError:
        number = 1
    
    try:
        page = paginator.page(number)
    except (EmptyPage, InvalidPage):
        page = paginator.page(paginator.num_pages)
        
    return paginator, page, number