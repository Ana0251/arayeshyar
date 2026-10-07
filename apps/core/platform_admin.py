"""پنل مدیریتی ساده و سفارشی آرایشیار برای مدیر پلتفرم."""
from functools import wraps

from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from apps.accounts.constants import Role
from apps.accounts.models import User
from apps.accounts.forms import AdminResetPasswordForm
from apps.booking.constants import AppointmentStatus
from apps.booking.models import Appointment
from apps.business.models import Business
from apps.customers.models import CustomerBusiness


def platform_admin_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect(f"/auth/login/?next={request.path}")
        if not (user.is_superuser or user.is_staff or user.role == Role.ADMIN):
            messages.error(request, "این بخش فقط برای مدیر پلتفرم است.")
            return redirect("core:home")
        return view(request, *args, **kwargs)
    return wrapped


@platform_admin_required
@require_GET
def control_dashboard(request):
    today = timezone.localdate()
    from apps.support.models import PasswordResetRequest
    from apps.blog.models import BlogPost
    context = {
        "open_password_requests": PasswordResetRequest.objects.filter(status="open").count(),
        "published_posts": BlogPost.objects.filter(status="published").count(),
        "businesses_count": Business.objects.count(),
        "active_businesses": Business.objects.filter(is_active=True, is_rejected=False).count(),
        "pending_businesses": Business.objects.filter(is_active=False, is_rejected=False).count(),
        "customers_count": User.objects.filter(role=Role.CUSTOMER).count(),
        "today_appointments": Appointment.objects.filter(start_at__date=today).count(),
        "pending_appointments": Appointment.objects.filter(status=AppointmentStatus.PENDING).count(),
        "recent_businesses": Business.objects.select_related("owner", "activity_type").order_by("-created_at")[:6],
        "recent_appointments": Appointment.objects.select_related("business", "customer", "staff").order_by("-created_at")[:8],
    }
    return render(request, "control/dashboard.html", context)


@platform_admin_required
@require_GET
def control_businesses(request):
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "all").strip()
    qs = Business.objects.select_related("owner", "activity_type", "target_audience").order_by("-created_at")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(owner__email__icontains=q) | Q(owner__phone__icontains=q) | Q(region__icontains=q))
    if status == "active":
        qs = qs.filter(is_active=True, is_rejected=False)
    elif status == "pending":
        qs = qs.filter(is_active=False, is_rejected=False)
    elif status == "rejected":
        qs = qs.filter(is_rejected=True)
    return render(request, "control/businesses.html", {"businesses": qs[:100], "q": q, "status": status})


@platform_admin_required
@require_GET
def control_business_detail(request, business_id):
    business = get_object_or_404(Business.objects.select_related("owner", "activity_type", "target_audience", "plan"), pk=business_id)
    stats = [
        ("کل نوبت‌ها", business.appointments.count()),
        ("مشتری‌ها", business.appointments.values("customer_id").distinct().count()),
        ("کارمند فعال", business.staff.filter(is_active=True).count()),
        ("خدمت فعال", business.services.filter(is_active=True).count()),
    ]
    recent = business.appointments.select_related("customer", "staff").order_by("-start_at")[:10]
    return render(request, "control/business_detail.html", {"business": business, "stats": stats, "recent": recent})


@platform_admin_required
@require_POST
def control_business_action(request, business_id, action):
    business = get_object_or_404(Business, pk=business_id)
    if action == "approve":
        business.is_active = True; business.is_rejected = False; business.rejection_reason = ""
        msg = "کسب‌وکار تأیید شد."
    elif action == "reject":
        business.is_active = False; business.is_rejected = True
        business.rejection_reason = (request.POST.get("reason") or "رد شده توسط مدیر").strip()[:500]
        msg = "کسب‌وکار رد شد."
    elif action == "deactivate":
        business.is_active = False
        msg = "کسب‌وکار غیرفعال شد."
    elif action == "activate":
        business.is_active = True; business.is_rejected = False
        msg = "کسب‌وکار فعال شد."
    else:
        messages.error(request, "عملیات نامعتبر است.")
        return redirect("control:business_detail", business_id=business.id)
    business.save(update_fields=["is_active", "is_rejected", "rejection_reason", "updated_at"])
    messages.success(request, msg)
    return redirect("control:business_detail", business_id=business.id)


@platform_admin_required
@require_GET
def control_customers(request):
    q = (request.GET.get("q") or "").strip()
    qs = User.objects.filter(role=Role.CUSTOMER).select_related("customer_profile").annotate(
        appointments_count=Count("appointments", distinct=True),
        businesses_count=Count("my_businesses", distinct=True),
    ).order_by("-date_joined")
    if q:
        qs = qs.filter(Q(email__icontains=q) | Q(phone__icontains=q) | Q(customer_profile__full_name__icontains=q))
    return render(request, "control/customers.html", {"customers": qs[:100], "q": q})


@platform_admin_required
@require_GET
def control_customer_detail(request, customer_id):
    customer = get_object_or_404(User.objects.select_related("customer_profile"), pk=customer_id, role=Role.CUSTOMER)
    appointments = customer.appointments.select_related("business", "staff").order_by("-start_at")[:30]
    businesses = CustomerBusiness.objects.filter(customer=customer).select_related("business").order_by("-last_visit_at", "-created_at")
    summary = {
        "total": customer.appointments.count(),
        "completed": customer.appointments.filter(status=AppointmentStatus.COMPLETED).count(),
        "cancelled": customer.appointments.filter(status=AppointmentStatus.CANCELLED).count(),
        "no_show": customer.appointments.filter(status=AppointmentStatus.NO_SHOW).count(),
    }
    return render(request, "control/customer_detail.html", {"customer_obj": customer, "appointments": appointments, "businesses": businesses, "summary": summary})


@platform_admin_required
@require_GET
def control_appointments(request):
    status = (request.GET.get("status") or "").strip()
    q = (request.GET.get("q") or "").strip()
    qs = Appointment.objects.select_related("business", "customer", "staff", "service").order_by("-start_at")
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(Q(business__name__icontains=q) | Q(customer__email__icontains=q) | Q(customer__phone__icontains=q) | Q(service_name_snapshot__icontains=q))
    return render(request, "control/appointments.html", {"appointments": qs[:150], "status": status, "q": q, "statuses": AppointmentStatus.choices})


@platform_admin_required
@require_http_methods(["GET", "POST"])
def control_reset_password(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    form = AdminResetPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        target.set_password(form.cleaned_data["new_password"])
        target.save(update_fields=["password"])
        messages.success(request, f"رمز عبور {target.display_name} با موفقیت تغییر کرد. ✅")
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        if hasattr(target, "business"):
            return redirect("control:business_detail", business_id=target.business.id)
        return redirect("control:customer_detail", customer_id=target.id)
    return render(request, "control/reset_password.html", {"target_user": target, "form": form})

@platform_admin_required
@require_GET
def control_password_requests(request):
    from apps.support.models import PasswordResetRequest
    status=(request.GET.get("status") or "open").strip()
    qs=PasswordResetRequest.objects.select_related("user","handled_by")
    if status in {"open","done","rejected"}: qs=qs.filter(status=status)
    return render(request,"control/password_requests.html",{"items":qs[:150],"status":status})

@platform_admin_required
@require_POST
def control_password_request_action(request, request_id):
    from apps.support.models import PasswordResetRequest
    obj=get_object_or_404(PasswordResetRequest,pk=request_id)
    action=request.POST.get("action")
    if action in {"done","rejected"}:
        obj.status=action; obj.handled_by=request.user; obj.handled_at=timezone.now()
        obj.save(update_fields=["status","handled_by","handled_at","updated_at"])
        messages.success(request,"وضعیت درخواست بروزرسانی شد.")
    return redirect("control:password_requests")

@platform_admin_required
@require_GET
def control_blog(request):
    from apps.blog.models import BlogPost
    q=(request.GET.get("q") or "").strip()
    qs=BlogPost.objects.select_related("author").order_by("-created_at")
    if q: qs=qs.filter(Q(title__icontains=q)|Q(body__icontains=q)|Q(category__icontains=q))
    return render(request,"control/blog_list.html",{"posts":qs[:150],"q":q})

@platform_admin_required
@require_http_methods(["GET","POST"])
def control_blog_create(request):
    from apps.blog.forms import BlogPostForm
    form=BlogPostForm(request.POST or None,request.FILES or None)
    if request.method=="POST" and form.is_valid():
        post=form.save(commit=False); post.author=request.user; post.save()
        messages.success(request,"مقاله ذخیره شد. ✅")
        return redirect("control:blog")
    return render(request,"control/blog_form.html",{"form":form,"page_title":"مقاله جدید"})

@platform_admin_required
@require_http_methods(["GET","POST"])
def control_blog_edit(request, post_id):
    from apps.blog.forms import BlogPostForm
    from apps.blog.models import BlogPost
    post=get_object_or_404(BlogPost,pk=post_id)
    form=BlogPostForm(request.POST or None,request.FILES or None,instance=post)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"مقاله بروزرسانی شد. ✅"); return redirect("control:blog")
    return render(request,"control/blog_form.html",{"form":form,"post":post,"page_title":"ویرایش مقاله"})

@platform_admin_required
@require_POST
def control_blog_delete(request, post_id):
    from apps.blog.models import BlogPost
    post=get_object_or_404(BlogPost,pk=post_id); post.delete(); messages.success(request,"مقاله حذف شد.")
    return redirect("control:blog")
