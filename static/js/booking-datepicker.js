/**
 * Persian DatePicker برای صفحه رزرو.
 */

(function () {
    'use strict';

    function initDatePicker() {
        const container = document.getElementById('date-picker-container');
        if (!container) {
            console.log('[BookingDatePicker] container پیدا نشد');
            return;
        }

        if (typeof customElements === 'undefined') {
            console.warn('[BookingDatePicker] Web Components پشتیبانی نمیشه.');
            return;
        }

        customElements.whenDefined('persian-datepicker-element').then(function () {
            console.log('[BookingDatePicker] Web Component آماده ست');

            const root = document.querySelector('[data-booking-datepicker]');
            const selectedDate = root?.dataset.selectedDate || '';
            const hasDate = root?.dataset.hasDate === '1';

            // ═══ ساخت Web Component ═══
            const picker = document.createElement('persian-datepicker-element');
            picker.setAttribute('placeholder', '۱۴۰۳/۰۷/۰۵');
            picker.setAttribute('format', 'YYYY/MM/DD');
            picker.setAttribute('rtl', 'true');
            // ⚠️ events-url رو نذار (تا درخواست نکنه)

            // ═══ listener ═══
            picker.addEventListener('change', function (event) {
                const detail = event.detail || {};
                let gregorian = null;

                if (detail.gregorian) {
                    gregorian = detail.gregorian;
                } else if (detail.jalali && typeof Jalali !== 'undefined') {
                    const gj = Jalali.toGregorian(
                        detail.jalali[0],
                        detail.jalali[1],
                        detail.jalali[2]
                    );
                    gregorian = [gj.gy, gj.gm, gj.gd];
                }

                if (gregorian && gregorian.length >= 3) {
                    const y = gregorian[0];
                    const m = String(gregorian[1]).padStart(2, '0');
                    const d = String(gregorian[2]).padStart(2, '0');
                    const url = new URL(window.location.href);
                    url.searchParams.set('date', `${y}-${m}-${d}`);
                    window.location.href = url.toString();
                }
            });

            container.appendChild(picker);

            // ═══ setValue بعد از append ═══
            if (hasDate && selectedDate && typeof Jalali !== 'undefined') {
                requestAnimationFrame(function () {
                    const parts = selectedDate.split('-').map(Number);
                    const j = Jalali.toJalali(parts[0], parts[1], parts[2]);
                    try {
                        if (typeof picker.setValue === 'function') {
                            picker.setValue(j.jy, j.jm, j.jd);
                            console.log('[BookingDatePicker] مقدار اولیه ست شد');
                        }
                    } catch (e) {
                        console.warn('[BookingDatePicker] setValue خطا:', e);
                    }
                });
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDatePicker);
    } else {
        initDatePicker();
    }
})();