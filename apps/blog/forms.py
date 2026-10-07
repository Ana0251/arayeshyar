from django import forms
from .models import BlogPost

BASE="w-full px-4 py-3 rounded-xl border border-black/10 bg-white focus:border-accent focus:ring-2 focus:ring-accent/20 outline-none"
class BlogPostForm(forms.ModelForm):
    published_at=forms.DateTimeField(label="تاریخ انتشار", required=False, input_formats=["%Y-%m-%dT%H:%M"], widget=forms.DateTimeInput(attrs={"class":BASE,"type":"datetime-local"}, format="%Y-%m-%dT%H:%M"))
    class Meta:
        model=BlogPost
        fields=["title","slug","excerpt","body","category","keywords","featured_image","meta_title","meta_description","status","published_at"]
        widgets={
            "title": forms.TextInput(attrs={"class":BASE}), "slug": forms.TextInput(attrs={"class":BASE,"dir":"ltr"}),
            "excerpt": forms.Textarea(attrs={"class":BASE,"rows":3}), "body": forms.Textarea(attrs={"class":BASE,"rows":16}),
            "category": forms.TextInput(attrs={"class":BASE}), "keywords": forms.TextInput(attrs={"class":BASE}),
            "featured_image": forms.FileInput(attrs={"class":BASE}), "meta_title": forms.TextInput(attrs={"class":BASE}),
            "meta_description": forms.Textarea(attrs={"class":BASE,"rows":3}), "status": forms.Select(attrs={"class":BASE}),
            "published_at": forms.DateTimeInput(attrs={"class":BASE,"type":"datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }
