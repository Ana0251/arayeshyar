from django.urls import path
from . import views
app_name="blog"
urlpatterns=[path("blog/",views.post_list,name="list"),path("blog/<uslug:slug>/",views.post_detail,name="detail")]
