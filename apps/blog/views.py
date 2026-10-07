from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET
from .models import BlogPost

@require_GET
def post_list(request):
    posts=BlogPost.objects.filter(status="published", published_at__lte=timezone.now()).order_by("-published_at")
    return render(request,"blog/list.html",{"posts":posts})

@require_GET
def post_detail(request,slug):
    post=get_object_or_404(BlogPost,status="published",published_at__lte=timezone.now(),slug=slug)
    return render(request,"blog/detail.html",{"post":post})
