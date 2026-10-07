"""
Views اپ support.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .constants import TicketStatus
from .forms import NewTicketForm, TicketReplyForm
from .models import Ticket, TicketAttachment, TicketMessage
from .selectors import get_ticket_by_id, get_user_tickets

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  New Ticket
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET", "POST"])
def new_ticket(request: HttpRequest) -> HttpResponse:
    """ایجاد تیکت جدید."""
    if request.method == "POST":
        form = NewTicketForm(request.POST, request.FILES)

        if form.is_valid():
            # ─── ساخت تیکت ───
            ticket = Ticket.objects.create(
                user=request.user,
                subject=form.cleaned_data["subject"],
                category=form.cleaned_data["category"],
                priority=form.cleaned_data["priority"],
                status=TicketStatus.OPEN,
            )

            # ─── پیام اول ───
            message = TicketMessage.objects.create(
                ticket=ticket,
                user=request.user,
                message=form.cleaned_data["message"],
                is_staff_reply=False,
            )

            # ─── فایل پیوست ───
            attachment = form.cleaned_data.get("attachment")
            if attachment:
                TicketAttachment.objects.create(
                    ticket_message=message,
                    file=attachment,
                    original_name=attachment.name,
                    file_size=attachment.size,
                )

            messages.success(
                request,
                _("تیکتت ثبت شد. ✅ به‌زودی بررسی میشه."),
            )

            logger.info(
                f"Ticket #{ticket.pk} created by {request.user.phone}"
            )

            return redirect("support:ticket_detail", ticket_id=ticket.pk)
    else:
        form = NewTicketForm()

    return render(
        request,
        "support/new_ticket.html",
        {"form": form},
    )


# ═══════════════════════════════════════════════════════════════
#  My Tickets
# ═══════════════════════════════════════════════════════════════


@login_required
@require_GET
def my_tickets(request: HttpRequest) -> HttpResponse:
    """لیست تیکت‌های کاربر."""
    tickets = get_user_tickets(request.user)

    return render(
        request,
        "support/my_tickets.html",
        {"tickets": tickets},
    )


# ═══════════════════════════════════════════════════════════════
#  Ticket Detail
# ═══════════════════════════════════════════════════════════════


@login_required
@require_http_methods(["GET", "POST"])
def ticket_detail(request: HttpRequest, ticket_id: int) -> HttpResponse:
    """جزئیات تیکت + پاسخ."""
    # ─── چک مالکیت ───
    ticket = get_object_or_404(Ticket, id=ticket_id)

    is_owner = ticket.user == request.user
    is_staff = request.user.is_staff

    if not (is_owner or is_staff):
        messages.error(request, _("دسترسی نداری."))
        return redirect("support:my_tickets")

    # ─── POST: پاسخ ───
    if request.method == "POST":
        if ticket.is_closed and not is_staff:
            messages.warning(
                request,
                _("این تیکت بسته شده. نمی‌تونی پاسخ بدی."),
            )
            return redirect("support:ticket_detail", ticket_id=ticket.pk)

        form = TicketReplyForm(request.POST, request.FILES)

        if form.is_valid():
            # ─── پیام ───
            message = TicketMessage.objects.create(
                ticket=ticket,
                user=request.user,
                message=form.cleaned_data["message"],
                is_staff_reply=is_staff,
            )

            # ─── فایل ───
            attachment = form.cleaned_data.get("attachment")
            if attachment:
                TicketAttachment.objects.create(
                    ticket_message=message,
                    file=attachment,
                    original_name=attachment.name,
                    file_size=attachment.size,
                )

            # ─── آپدیت وضعیت ───
            if is_staff:
                ticket.status = TicketStatus.ANSWERED
                ticket.save(update_fields=["status", "updated_at"])
            else:
                # ─── کاربر پاسخ داده، تیکت برمی‌گرده به «باز» ───
                if ticket.status in (TicketStatus.ANSWERED, TicketStatus.CLOSED):
                    ticket.status = TicketStatus.OPEN
                    ticket.closed_at = None
                    ticket.save(update_fields=["status", "closed_at", "updated_at"])

            messages.success(request, _("پاسخت ثبت شد. ✅"))
            return redirect("support:ticket_detail", ticket_id=ticket.pk)
    else:
        form = TicketReplyForm()

    # ─── علامت‌گذاری پیام‌ها به‌عنوان خوانده‌شده ───
    if is_owner:
        ticket.messages.filter(
            is_read=False,
            is_staff_reply=True,
        ).update(is_read=True)

    ticket_messages = ticket.messages.select_related("user").prefetch_related(
        "attachments"
    )

    return render(
        request,
        "support/ticket_detail.html",
        {
            "ticket": ticket,
            "messages_list": ticket_messages,
            "form": form,
            "is_owner": is_owner,
            "is_staff": is_staff,
        },
    )


# ═══════════════════════════════════════════════════════════════
#  Close Ticket
# ═══════════════════════════════════════════════════════════════


@login_required
@require_POST
def close_ticket(request: HttpRequest, ticket_id: int) -> HttpResponse:
    """بستن تیکت (فقط صاحب یا staff)."""
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if ticket.user != request.user and not request.user.is_staff:
        messages.error(request, _("دسترسی نداری."))
        return redirect("support:my_tickets")

    ticket.close()
    messages.success(request, _("تیکت بسته شد."))

    return redirect("support:ticket_detail", ticket_id=ticket.pk)
@require_http_methods(["GET", "POST"])
def password_help(request: HttpRequest) -> HttpResponse:
    """ثبت درخواست بازیابی رمز بدون نیاز به لاگین/OTP."""
    from apps.accounts.models import User
    from .forms import PasswordHelpForm
    from .models import PasswordResetRequest
    form=PasswordHelpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        phone=form.cleaned_data["phone"]
        # از ایجاد اسپم تکراری باز جلوگیری می‌کنیم.
        existing=PasswordResetRequest.objects.filter(phone=phone,status="open").first()
        if existing:
            messages.info(request, _("درخواست بازیابی این شماره قبلاً ثبت شده و در صف بررسیه."))
            return render(request,"support/password_help_done.html",{"request_obj":existing})
        user=User.objects.filter(phone=phone).first()
        obj=PasswordResetRequest.objects.create(
            phone=phone, full_name=form.cleaned_data["full_name"].strip(),
            note=form.cleaned_data.get("note","").strip(), user=user,
        )
        logger.info("Password reset request #%s for %s",obj.pk,phone)
        return render(request,"support/password_help_done.html",{"request_obj":obj})
    return render(request,"support/password_help.html",{"form":form})
