/**
 * رزرو: اتصال تقویم شمسی به بارگذاری ساعت‌های آزاد.
 *
 * نکته مهم: listener به صورت delegated روی document است تا حتی بعد از HTMX swap
 * و upgrade شدن Web Component هم event انتخاب تاریخ از دست نرود.
 */
(function () {
    'use strict';

    const VERSION = '20261006-5';
    console.info('[BookingDatePicker] loaded', VERSION);

    function pad2(value) {
        return String(value).padStart(2, '0');
    }

    function normalizeGregorian(value) {
        if (!value) return '';

        if (Array.isArray(value) && value.length >= 3) {
            return `${value[0]}-${pad2(value[1])}-${pad2(value[2])}`;
        }

        if (typeof value === 'object') {
            const y = value.year ?? value.gy ?? value[0];
            const m = value.month ?? value.gm ?? value[1];
            const d = value.day ?? value.gd ?? value[2];
            if (y && m && d) return `${y}-${pad2(m)}-${pad2(d)}`;
        }

        if (typeof value === 'string') {
            const match = value.match(/^(\d{4})[-\/]?(\d{1,2})[-\/]?(\d{1,2})/);
            if (match) return `${match[1]}-${pad2(match[2])}-${pad2(match[3])}`;
        }

        return '';
    }

    function gregorianFromEvent(event) {
        const detail = event.detail || {};

        let result = normalizeGregorian(detail.gregorian);
        if (result) return result;

        result = normalizeGregorian(detail.value) || normalizeGregorian(detail.isoString);
        if (result) return result;

        if (Array.isArray(detail.jalali) && detail.jalali.length >= 3 && window.Jalali) {
            const g = window.Jalali.toGregorian(
                Number(detail.jalali[0]),
                Number(detail.jalali[1]),
                Number(detail.jalali[2])
            );
            return `${g.gy}-${pad2(g.gm)}-${pad2(g.gd)}`;
        }

        return '';
    }

    function getBookingRoot(node) {
        return node?.closest?.('#booking-flow') || document.querySelector('#booking-flow');
    }

    function getTarget() {
        return document.getElementById('booking-date-results');
    }

    function buildSlotsUrl(root, dateValue) {
        const url = new URL(window.location.pathname, window.location.origin);
        const station = root?.dataset.selectedStation || '';
        const service = root?.dataset.selectedService || '';
        const staff = root?.dataset.selectedStaff || '';

        if (station) url.searchParams.set('station', station);
        if (service) url.searchParams.set('service', service);
        if (staff) url.searchParams.set('staff', staff);
        url.searchParams.set('date', dateValue);
        url.searchParams.set('slots_only', '1');
        return url;
    }

    function updateBrowserUrl(root, dateValue) {
        const url = new URL(window.location.href);
        const station = root?.dataset.selectedStation || '';
        const service = root?.dataset.selectedService || '';
        const staff = root?.dataset.selectedStaff || '';

        station ? url.searchParams.set('station', station) : url.searchParams.delete('station');
        service ? url.searchParams.set('service', service) : url.searchParams.delete('service');
        staff ? url.searchParams.set('staff', staff) : url.searchParams.delete('staff');
        url.searchParams.set('date', dateValue);
        url.searchParams.delete('slots_only');
        history.replaceState({}, '', url.toString());
    }

    function showLoading(target) {
        if (!target) return;
        target.innerHTML = `
            <div class="bg-white rounded-2xl shadow-md mb-5 p-6 text-center" role="status">
                <div class="inline-block w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
                <p class="text-sm text-darktext/60 mt-2">در حال دریافت ساعت‌های آزاد...</p>
            </div>`;
    }

    function showError(target, message) {
        if (!target) return;
        target.innerHTML = `
            <div class="bg-white rounded-2xl shadow-md mb-5 p-6 text-center">
                <div class="text-3xl mb-2">⚠️</div>
                <p class="text-sm font-bold text-danger">${message || 'دریافت ساعت‌های آزاد انجام نشد.'}</p>
                <p class="text-xs text-darktext/50 mt-1">تاریخ رو دوباره انتخاب کن.</p>
            </div>`;
    }

    async function loadSlots(root, dateValue) {
        const target = getTarget();
        if (!root) {
            showError(target, 'اطلاعات رزرو پیدا نشد.');
            return;
        }
        if (!root.dataset.selectedService) {
            showError(target, 'اول خدمت رو انتخاب کن.');
            return;
        }
        if (!dateValue) {
            showError(target, 'تاریخ انتخاب‌شده قابل تشخیص نبود.');
            return;
        }

        const hiddenDate = root.querySelector('[data-booking-date-input]');
        if (hiddenDate) hiddenDate.value = dateValue;
        root.dataset.selectedDate = dateValue;

        // Alpine state را هم بدون وابستگی به re-render همگام می‌کنیم.
        try {
            root.dispatchEvent(new CustomEvent('booking-date-selected', {
                bubbles: false,
                detail: { date: dateValue }
            }));
        } catch (_) {}

        const url = buildSlotsUrl(root, dateValue);
        updateBrowserUrl(root, dateValue);
        showLoading(target);

        console.info('[BookingDatePicker] loading slots', url.toString());

        try {
            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'HX-Request': 'true',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                cache: 'no-store'
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const html = await response.text();
            target.innerHTML = html;

            // به HTMX/Alpine اطلاع بده محتوای جدید وارد DOM شده.
            if (window.htmx) window.htmx.process(target);
            document.dispatchEvent(new CustomEvent('booking:slots-loaded', {
                detail: { date: dateValue }
            }));
        } catch (error) {
            console.error('[BookingDatePicker] slots request failed', error);
            showError(target);
        }
    }

    // Delegated listener: مستقل از زمان init و HTMX swap.
    document.addEventListener('change', function (event) {
        const picker = event.target;
        if (!picker?.matches?.('[data-booking-persian-picker]')) return;

        console.info('[BookingDatePicker] picker change', event.detail);
        const dateValue = gregorianFromEvent(event);
        if (!dateValue) {
            console.error('[BookingDatePicker] Gregorian date missing', event.detail);
            showError(getTarget(), 'تاریخ انتخاب‌شده قابل تشخیص نبود.');
            return;
        }

        loadSlots(getBookingRoot(picker), dateValue);
    }, true);

    async function restorePickerValue(root) {
        const picker = root?.querySelector?.('[data-booking-persian-picker]');
        if (!picker || picker.dataset.bookingRestoreDone === '1') return;
        picker.dataset.bookingRestoreDone = '1';

        const gregorian = picker.dataset.gregorianValue || '';
        if (!/^\d{4}-\d{2}-\d{2}$/.test(gregorian) || !window.Jalali) return;

        try {
            await customElements.whenDefined('persian-datepicker-element');
            const [gy, gm, gd] = gregorian.split('-').map(Number);
            const j = window.Jalali.toJalali(gy, gm, gd);
            picker.setValue?.(j.jy, j.jm, j.jd);
        } catch (error) {
            console.warn('[BookingDatePicker] restore failed', error);
        }
    }

    function boot(root) {
        const bookingRoot = root?.matches?.('#booking-flow')
            ? root
            : root?.querySelector?.('#booking-flow') || document.querySelector('#booking-flow');
        if (bookingRoot) restorePickerValue(bookingRoot);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => boot(document));
    } else {
        boot(document);
    }

    document.body.addEventListener('htmx:afterSwap', event => boot(event.detail?.target || document));
    document.body.addEventListener('htmx:afterSettle', event => boot(event.detail?.target || document));
})();
