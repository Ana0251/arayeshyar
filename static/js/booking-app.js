/**
 * Alpine.js component برای صفحه رزرو.
 * انتخاب مرحله‌ها با HTMX انجام می‌شود؛ Alpine فقط state محلی ساعت را نگه می‌دارد.
 */
function bookingApp() {
    return {
        selectedTime: '',
        selectedServiceId: null,
        selectedStaffId: null,
        selectedDate: '',

        init() {
            const el = this.$root;
            this.selectedServiceId = el.dataset.selectedService
                ? parseInt(el.dataset.selectedService, 10)
                : null;
            this.selectedStaffId = el.dataset.selectedStaff
                ? parseInt(el.dataset.selectedStaff, 10)
                : null;
            this.selectedDate = el.dataset.selectedDate || '';
        },

        selectTime(timeStr) {
            this.selectedTime = timeStr;
        },

        get startAt() {
            if (!this.selectedTime || !this.selectedDate) return '';
            return `${this.selectedDate}T${this.selectedTime}:00`;
        },

        get canSubmit() {
            return Boolean(this.selectedTime && this.selectedServiceId && this.selectedDate);
        },
    };
}
