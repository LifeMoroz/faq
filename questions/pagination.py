# coding=utf-8
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def get_page(request, model, count=20, query=None):
    """
    Returns the page
    """
    if not query:
        query = model.objects.all()
    paginator = Paginator(query, count)
    page_number = request.GET.get('page', '1')

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return page
