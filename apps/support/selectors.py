"""
Selectors — کوئری‌های خواندنی اپ support.
"""

from django.db.models import Count, Q, QuerySet

from .constants import TicketStatus
from .models import Ticket


def get_user_tickets(user) -> QuerySet[Ticket]:
    """
    تیکت‌های یه کاربر.

    ─── نکته: ───
    از `msg_count` به جای `messages_count` استفاده می‌کنیم
    تا با property `Ticket.messages_count` تداخل نکنه.
    """
    return (
        Ticket.objects.filter(user=user)
        .annotate(msg_count=Count("messages"))
        .order_by("-last_reply_at", "-created_at")
    )


def get_ticket_by_id(ticket_id: int, user=None) -> Ticket | None:
    """گرفتن تیکت با ID (اختیاری: چک مالکیت)."""
    qs = Ticket.objects.all()
    if user:
        qs = qs.filter(Q(user=user) | Q(is_staff=user.is_staff))
    return qs.filter(id=ticket_id).first()


def get_open_tickets_count(user) -> int:
    """تعداد تیکت‌های باز کاربر."""
    return Ticket.objects.filter(
        user=user,
    ).exclude(
        status=TicketStatus.CLOSED,
    ).count()