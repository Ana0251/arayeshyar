/**
 * Persian Datepicker Element — Wrapper برای Django.
 */

(function () {
    'use strict';

    console.log('✅ [date-picker.js] لود شد');

    function pad2(n) {
        return String(n).padStart(2, '0');
    }

    function initOne(input) {
        if (input.hasAttribute('data-persian-init')) return;
        input.setAttribute('data-persian-init', '1');

        if (typeof customElements === 'undefined') {
            console.warn('[DatePicker] Web Components پشتیبانی نمیشه.');
            return;
        }

        // ─── name رو به hidden منتقل کن ───
        var fieldName = input.getAttribute('name') || 'date';
        input.removeAttribute('name');

        // ─── ⚡ required رو بردار (input مخفی میشه و focus نمی‌گیره) ───
        input.removeAttribute('required');

        // ─── input اصلی رو مخفی کن ───
        input.style.display = 'none';

        // ─── hidden input ───
        var hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = fieldName;

        var initialGregorian = input.value;
        if (initialGregorian && /^\d{4}-\d{2}-\d{2}$/.test(initialGregorian)) {
            hiddenInput.value = initialGregorian;
        }

        // ─── Web Component ───
        var picker = document.createElement('persian-datepicker-element');
        picker.setAttribute('placeholder', '۱۴۰۳/۰۷/۰۵');
        picker.setAttribute('format', 'YYYY/MM/DD');
        picker.setAttribute('rtl', 'true');
        picker.setAttribute('events-url', '');

        // ─── مقدار اولیه ───
        if (initialGregorian && /^\d{4}-\d{2}-\d{2}$/.test(initialGregorian)) {
            if (typeof Jalali !== 'undefined') {
                var parts = initialGregorian.split('-').map(Number);
                var j = Jalali.toJalali(parts[0], parts[1], parts[2]);
                try {
                    if (typeof picker.setValue === 'function') {
                        picker.setValue(j.jy, j.jm, j.jd);
                    }
                } catch (e) {}
            }
        }

        // ─── listener برای تغییر ───
        picker.addEventListener('change', function (event) {
            var detail = event.detail || {};
            var gregorian = detail.gregorian || (Array.isArray(detail.value) ? detail.value : null);

            if (gregorian && gregorian.length >= 3) {
                hiddenInput.value =
                    gregorian[0] + '-' +
                    pad2(gregorian[1]) + '-' +
                    pad2(gregorian[2]);
            } else if (detail.jalali && typeof Jalali !== 'undefined') {
                var gj = Jalali.toGregorian(
                    detail.jalali[0],
                    detail.jalali[1],
                    detail.jalali[2]
                );
                hiddenInput.value =
                    gj.gy + '-' + pad2(gj.gm) + '-' + pad2(gj.gd);
            }
        });

        // ─── insert ───
        input.parentNode.insertBefore(hiddenInput, input.nextSibling);
        input.parentNode.insertBefore(picker, hiddenInput.nextSibling);
    }

    function initPickers(root) {
        root = root || document;
        var inputs = root.querySelectorAll(
            'input[data-persian-datepicker]:not([data-persian-init])'
        );
        inputs.forEach(initOne);
    }

    // ─── Bootstrap ───
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            initPickers();
        });
    } else {
        initPickers();
    }

    document.body.addEventListener('htmx:afterSwap', function (evt) {
        initPickers(evt.detail.target);
    });

    window.PersianDatePicker = { init: initPickers };
})();