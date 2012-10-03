from django.views.decorators.cache import never_cache
from django.views.generic.simple import direct_to_template


@never_cache
def search(request):
    """Crud handles everything."""
    return direct_to_template(request, 'search/search.html')
