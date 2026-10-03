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

        for (var m = 0; m < 60; m += minuteStep) {
            var mm = pad2(m);
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
        var inputs = root.querySelectorAll(
            'input[type="time"][data-time-picker]:not([data-time-init])'
        );
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
        initTimePickers(evt.detail.target);
    });

    window.TimePicker = { init: initTimePickers };
})();