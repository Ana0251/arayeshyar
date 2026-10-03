/**
 * Alpine.js component برای صفحه‌ی انتخاب فعالیت (register).
 *
 * ─── استفاده توی template: ───
 *   <div x-data="activityForm()">
 *
 * ─── چرا این الگو؟ ───
 * چون Django template syntax ({{ }}) توی inline JS با IDE conflict داره.
 */

function activityForm() {
    return {
        showOther: false,
        otherValue: '',

        /**
         * انتخاب یه فعالیت از لیست.
         * فرم رو با activity_id پر می‌کنه و submit می‌کنه.
         */
        selectActivity(activityId) {
            const form = document.getElementById('activity-form');
            const activityInput = document.getElementById('selected-activity-id');
            const otherInput = form.querySelector('input[name="other_activity"]');

            if (activityInput) activityInput.value = activityId;
            if (otherInput) otherInput.value = '';

            form.submit();
        },

        /**
         * ثبت یه فعالیت سفارشی (سایر).
         */
        submitOther() {
            const form = document.getElementById('activity-form');
            const activityInput = document.getElementById('selected-activity-id');
            const otherInput = form.querySelector('input[name="other_activity"]');

            const value = (this.otherValue || '').trim();
            if (!value) {
                this.showAlert('لطفاً نام فعالیتت رو وارد کن');
                return;
            }

            if (activityInput) activityInput.value = '';
            if (otherInput) otherInput.value = value;

            form.submit();
        },

        showAlert(message) {
            if (window.showToast) {
                window.showToast(message, 'warning');
            } else {
                alert(message);
            }
        },
    };
}