/**
 * Time Picker — دو تا dropdown زیبا برای ساعت و دقیقه.
 */

(function () {
    'use strict';

    function pad2(n) {
        return String(n).padStart(2, '0');
    }

    function initTimePicker(input) {
        if (input.hasAttribute('data-time-init')) return;
        input.setAttribute('data-time-init', '1');

        // ─── گام دقیقه ───
        var minuteStep = parseInt(input.getAttribute('data-minute-step') || '15', 10);
        if (minuteStep < 1 || minuteStep > 60) minuteStep = 15;

        // ─── مقدار اولیه ───
        var initialValue = input.value || '';
        var initHour = '';
        var initMinute = '';

        if (initialValue && /^\d{1,2}:\d{2}/.test(initialValue)) {
            var parts = initialValue.split(':');
            initHour = pad2(parseInt(parts[0], 10));
            initMinute = pad2(parseInt(parts[1], 10));
        }

        var wasRequired = input.hasAttribute('required');

        // ─── ⚡ required رو حذف کن (چون input مخفی میشه و مرورگر نمیتونه focus کنه) ───
        input.removeAttribute('required');

        // ─── input رو مخفی کن ───
        input.style.display = 'none';
        input.removeAttribute('name');

        // ─── hidden input ───
        var hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = input.getAttribute('data-name') || 'time';
        hiddenInput.value = initHour && initMinute ? initHour + ':' + initMinute : '';

        // ─── wrapper ───
        var wrapper = document.createElement('div');
        wrapper.className = 'time-picker-wrapper';

        // ═══════════════════════════════════════════════════════════
        //  ساعت
        // ═══════════════════════════════════════════════════════════

        var hourSelect = document.createElement('select');
        hourSelect.className = 'time-picker-select';
        hourSelect.setAttribute('dir', 'ltr');

        var hourPlaceholder = document.createElement('option');
        hourPlaceholder.value = '';
        hourPlaceholder.textContent = 'ساعت';
        hourSelect.appendChild(hourPlaceholder);

        for (var h = 0; h < 24; h++) {
            var hh = pad2(h);
            var opt = document.createElement('option');
            opt.value = hh;
            opt.textContent = hh;
            if (hh === initHour) opt.selected = true;
            hourSelect.appendChild(opt);
        }

        // ═══════════════════════════════════════════════════════════
        //  دقیقه
        // ═══════════════════════════════════════════════════════════

        var minuteSelect = document.createElement('select');
        minuteSelect.className = 'time-picker-select';
        minuteSelect.setAttribute('dir', 'ltr');

        var minutePlaceholder = document.createElement('option');
        minutePlaceholder.value = '';
        minutePlaceholder.textContent = 'دقیقه';
        minuteSelect.appendChild(minutePlaceholder);

        // اگر مقدار فعلی روی گام ۱۵ دقیقه‌ای نبود (مثلاً 09:10)، همان دقیقه را هم اضافه کن
        var minuteValues = [];
        for (var mv = 0; mv < 60; mv += minuteStep) minuteValues.push(pad2(mv));
        if (initMinute && minuteValues.indexOf(initMinute) === -1) {
            minuteValues.push(initMinute);
            minuteValues.sort();
        }

        for (var mi = 0; mi < minuteValues.length; mi++) {
            var mm = minuteValues[mi];
            var opt2 = document.createElement('option');
            opt2.value = mm;
            opt2.textContent = mm;
            if (mm === initMinute) opt2.selected = true;
            minuteSelect.appendChild(opt2);
        }

        // ═══════════════════════════════════════════════════════════
        //  Event Listener
        // ═══════════════════════════════════════════════════════════

        function updateValue() {
            var hVal = hourSelect.value;
            var mVal = minuteSelect.value;

            if (hVal && mVal) {
                hiddenInput.value = hVal + ':' + mVal;
            } else {
                hiddenInput.value = '';
            }
        }

        if (wasRequired) {
            hourSelect.required = true;
            minuteSelect.required = true;
        }

        hourSelect.addEventListener('change', updateValue);
        minuteSelect.addEventListener('change', updateValue);

        // ═══════════════════════════════════════════════════════════
        //  Insert
        // ═══════════════════════════════════════════════════════════

        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(hourSelect);
        wrapper.appendChild(minuteSelect);
        wrapper.appendChild(hiddenInput);
        wrapper.appendChild(input);
    }

    function initTimePickers(root) {
        root = root || document;
        var inputs = [];
        if (root.matches && root.matches('input[type="time"][data-time-picker]:not([data-time-init])')) {
            inputs.push(root);
        }
        if (root.querySelectorAll) {
            root.querySelectorAll('input[type="time"][data-time-picker]:not([data-time-init])').forEach(function (el) {
                if (inputs.indexOf(el) === -1) inputs.push(el);
            });
        }
        inputs.forEach(initTimePicker);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            initTimePickers();
        });
    } else {
        initTimePickers();
    }

    document.body.addEventListener('htmx:afterSwap', function (evt) {
        initTimePickers(evt.detail && evt.detail.target ? evt.detail.target : document);
    });
    document.body.addEventListener('htmx:afterSettle', function (evt) {
        initTimePickers(evt.detail && evt.detail.target ? evt.detail.target : document);
    });

    // reset() روی فرم، selectهای سفارشی را به حالت اولیه برمی‌گرداند.
    document.addEventListener('reset', function (event) {
        var form = event.target;
        if (!form || !form.matches || !form.matches('form')) return;
        setTimeout(function () {
            form.querySelectorAll('.time-picker-wrapper').forEach(function (wrapper) {
                var original = wrapper.querySelector('input[data-time-picker]');
                var selects = wrapper.querySelectorAll('select.time-picker-select');
                var hidden = wrapper.querySelector('input[type="hidden"]');
                var raw = original ? (original.defaultValue || '') : '';
                var hour = '', minute = '';
                if (/^\d{1,2}:\d{2}/.test(raw)) {
                    var parts = raw.split(':');
                    hour = pad2(parseInt(parts[0], 10));
                    minute = pad2(parseInt(parts[1], 10));
                }
                if (selects[0]) selects[0].value = hour;
                if (selects[1]) selects[1].value = minute;
                if (hidden) hidden.value = hour && minute ? hour + ':' + minute : '';
            });
        }, 0);
    });

    window.TimePicker = { init: initTimePickers };
})();