from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.constants import Role
from apps.accounts.models import User
from apps.booking.constants import AppointmentStatus
from apps.booking.models import Appointment, BlockedCustomer
from apps.core.decorators import business_required


@business_required
@require_GET
def manage_customers(request):
    business = request.user.business
    q = (request.GET.get("q") or "").strip()
    customer_ids = business.appointments.values_list("customer_id", flat=True).distinct()
    qs = User.objects.filter(id__in=customer_ids, role=Role.CUSTOMER).select_related("customer_profile").annotate(
        total_appointments=Count("appointments", filter=Q(appointments__business=business), distinct=True),
        completed_count=Count("appointments", filter=Q(appointments__business=business, appointments__status=AppointmentStatus.COMPLETED), distinct=True),
        cancelled_count=Count("appointments", filter=Q(appointments__business=business, appointments__status=AppointmentStatus.CANCELLED), distinct=True),
        no_show_count=Count("appointments", filter=Q(appointments__business=business, appointments__status=AppointmentStatus.NO_SHOW), distinct=True),
    ).order_by("-total_appointments")
    if q:
        qs = qs.filter(Q(email__icontains=q) | Q(phone__icontains=q) | Q(customer_profile__full_name__icontains=q))
    blocked_phones = set(business.blocked_customers.values_list("phone", flat=True))
    rows = [{"customer": c, "is_blocked": bool(c.phone and c.phone in blocked_phones)} for c in qs]
    return render(request, "business/manage_customers.html", {"business": business, "rows": rows, "q": q})


@business_required
@require_GET
def customer_detail(request, customer_id):
    business = request.user.business
    valid_customer_ids = business.appointments.values_list("customer_id", flat=True).distinct()
    customer = get_object_or_404(
        User.objects.select_related("customer_profile"),
        pk=customer_id, role=Role.CUSTOMER, id__in=valid_customer_ids,
    )
    appointments = Appointment.objects.filter(business=business, customer=customer).select_related("service", "staff").order_by("-start_at")
    block = BlockedCustomer.objects.filter(business=business, phone=customer.phone).first() if customer.phone else None
    summary = {
        "total": appointments.count(),
        "completed": appointments.filter(status=AppointmentStatus.COMPLETED).count(),
        "cancelled": appointments.filter(status=AppointmentStatus.CANCELLED).count(),
        "no_show": appointments.filter(status=AppointmentStatus.NO_SHOW).count(),
    }
    return render(request, "business/customer_detail.html", {"business": business, "customer_obj": customer, "appointments": appointments[:50], "summary": summary, "block": block})


@business_required
@require_POST
def toggle_customer_block(request, customer_id):
    business = request.user.business
    valid_customer_ids = business.appointments.values_list("customer_id", flat=True).distinct()
    customer = get_object_or_404(User, pk=customer_id, role=Role.CUSTOMER, id__in=valid_customer_ids)
    if not customer.phone:
        messages.error(request, "این مشتری شماره موبایل ثبت‌شده ندارد.")
        return redirect("business:customer_detail", customer_id=customer.id)
    obj = BlockedCustomer.objects.filter(business=business, phone=customer.phone).first()
    if obj:
        obj.delete(); messages.success(request, "مشتری از لیست مسدودها خارج شد.")
    else:
        BlockedCustomer.objects.create(business=business, phone=customer.phone, name=customer.display_name, reason=(request.POST.get("reason") or "مسدود شده از پنل مشتری‌ها")[:200])
        messages.success(request, "مشتری مسدود شد و نمی‌تواند نوبت جدید بگیرد.")
    return redirect("business:customer_detail", customer_id=customer.id)
