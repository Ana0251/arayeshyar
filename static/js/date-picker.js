/**
 * Persian Datepicker Element — Wrapper عمومی فرم‌های Django.
 *
 * - کاربر تاریخ شمسی می‌بیند.
 * - backend مقدار میلادی Y-m-d دریافت می‌کند.
 * - بعد از HTMX و reset فرم دوباره sync می‌شود.
 */
(function () {
    'use strict';

    function pad2(n) {
        return String(n).padStart(2, '0');
    }

    function normalizeGregorian(value) {
        if (!value) return '';
        if (Array.isArray(value) && value.length >= 3) {
            return value[0] + '-' + pad2(value[1]) + '-' + pad2(value[2]);
        }
        if (typeof value === 'string') {
            const m = value.match(/^(\d{4})[-\/]?(\d{1,2})[-\/]?(\d{1,2})/);
            return m ? m[1] + '-' + pad2(m[2]) + '-' + pad2(m[3]) : '';
        }
        return '';
    }

    function eventGregorian(event) {
        const detail = event.detail || {};
        let value = normalizeGregorian(detail.gregorian) || normalizeGregorian(detail.value) || normalizeGregorian(detail.isoString);
        if (value) return value;

        if (Array.isArray(detail.jalali) && detail.jalali.length >= 3 && window.Jalali) {
            const g = Jalali.toGregorian(detail.jalali[0], detail.jalali[1], detail.jalali[2]);
            return g.gy + '-' + pad2(g.gm) + '-' + pad2(g.gd);
        }
        return '';
    }

    async function setPickerGregorian(picker, gregorian) {
        if (!picker || !gregorian || !/^\d{4}-\d{2}-\d{2}$/.test(gregorian) || !window.Jalali) return;
        if (window.customElements?.whenDefined) {
            try { await customElements.whenDefined('persian-datepicker-element'); } catch (_) {}
        }
        const parts = gregorian.split('-').map(Number);
        const j = Jalali.toJalali(parts[0], parts[1], parts[2]);
        try {
            if (typeof picker.setValue === 'function') picker.setValue(j.jy, j.jm, j.jd);
        } catch (_) {}
    }

    function initOne(input) {
        if (!input || input.hasAttribute('data-persian-init')) return;
        input.setAttribute('data-persian-init', '1');

        if (typeof customElements === 'undefined') {
            console.warn('[DatePicker] Web Components پشتیبانی نمی‌شود.');
            return;
        }

        const fieldName = input.getAttribute('name') || input.getAttribute('data-name') || 'date';
        const initialGregorian = input.value || '';
        const wasRequired = input.required;

        input.dataset.originalName = fieldName;
        input.removeAttribute('name');
        input.removeAttribute('required');
        input.style.display = 'none';

        const wrapper = document.createElement('div');
        wrapper.className = 'persian-datepicker-wrapper';
        wrapper.dataset.persianWrapper = '1';

        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = fieldName;
        hiddenInput.value = /^\d{4}-\d{2}-\d{2}$/.test(initialGregorian) ? initialGregorian : '';
        hiddenInput.dataset.persianHidden = '1';
        if (wasRequired) hiddenInput.dataset.required = '1';

        const picker = document.createElement('persian-datepicker-element');
        picker.setAttribute('placeholder', 'انتخاب تاریخ');
        picker.setAttribute('format', 'YYYY/MM/DD');
        picker.setAttribute('rtl', 'true');
        picker.setAttribute('show-events', 'false');
        picker.dataset.persianGenerated = '1';

        picker.addEventListener('change', function (event) {
            const gregorian = eventGregorian(event);
            if (!gregorian) {
                console.warn('[DatePicker] تاریخ میلادی از event استخراج نشد.', event.detail);
                return;
            }
            hiddenInput.value = gregorian;
            hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
            input.dispatchEvent(new CustomEvent('persian-date-change', {
                bubbles: true,
                detail: { gregorian: gregorian }
            }));
        });

        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        wrapper.appendChild(hiddenInput);
        wrapper.appendChild(picker);

        setPickerGregorian(picker, initialGregorian);
    }

    function getInputs(root) {
        const items = [];
        if (root?.matches?.('input[data-persian-datepicker]:not([data-persian-init])')) items.push(root);
        root?.querySelectorAll?.('input[data-persian-datepicker]:not([data-persian-init])').forEach(function (el) {
            if (!items.includes(el)) items.push(el);
        });
        return items;
    }

    function initPickers(root) {
        (getInputs(root || document)).forEach(initOne);
    }

    function syncAfterReset(form) {
        setTimeout(function () {
            form.querySelectorAll('[data-persian-wrapper]').forEach(function (wrapper) {
                const original = wrapper.querySelector('input[data-persian-datepicker]');
                const hidden = wrapper.querySelector('[data-persian-hidden]');
                const picker = wrapper.querySelector('[data-persian-generated]');
                const value = original?.defaultValue || '';
                if (hidden) hidden.value = /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : '';
                if (picker) {
                    if (value) setPickerGregorian(picker, value);
                    else {
                        try {
                            if (picker.shadowRoot) {
                                const visualInput = picker.shadowRoot.querySelector('input');
                                if (visualInput) visualInput.value = '';
                            }
                        } catch (_) {}
                    }
                }
            });
        }, 0);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () { initPickers(document); });
    } else {
        initPickers(document);
    }

    document.body.addEventListener('htmx:afterSwap', function (evt) {
        initPickers(evt.detail?.target || document);
    });
    document.body.addEventListener('htmx:afterSettle', function (evt) {
        initPickers(evt.detail?.target || document);
    });
    document.addEventListener('reset', function (event) {
        if (event.target?.matches?.('form')) syncAfterReset(event.target);
    });

    window.PersianDatePicker = { init: initPickers };
})();
