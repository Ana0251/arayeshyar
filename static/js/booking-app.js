/**
 * Alpine.js component برای صفحه رزرو.
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
            console.log('[bookingApp] init:', this.selectedServiceId);
        },

        selectStation(stationId) {
            console.log('[bookingApp] selectStation:', stationId);
            const url = new URL(window.location.href);
            if (stationId) {
                url.searchParams.set('station', stationId);
            } else {
                url.searchParams.delete('station');
            }
            url.searchParams.delete('service');
            url.searchParams.delete('staff');
            window.location.href = url.toString();
        },

        selectService(serviceId) {
            console.log('[bookingApp] selectService:', serviceId);
            const url = new URL(window.location.href);
            url.searchParams.set('service', serviceId);
            url.searchParams.delete('staff');
            window.location.href = url.toString();
        },

        selectStaff(staffId) {
            console.log('[bookingApp] selectStaff:', staffId);
            const url = new URL(window.location.href);
            if (staffId) {
                url.searchParams.set('staff', staffId);
            } else {
                url.searchParams.delete('staff');
            }
            window.location.href = url.toString();
        },

        selectTime(timeStr) {
            console.log('[bookingApp] selectTime:', timeStr);
            this.selectedTime = timeStr;
        },

        get startAt() {
            if (!this.selectedTime || !this.selectedDate) return '';
            return `${this.selectedDate}T${this.selectedTime}:00`;
        },

        get canSubmit() {
            return Boolean(this.selectedTime && this.selectedServiceId);
        },

        submitForm(event) {
            const form = event.target;

            if (!this.selectedServiceId) {
                this.showAlert('لطفاً یه خدمت انتخاب کن');
                return;
            }
            if (!this.selectedTime) {
                this.showAlert('لطفاً یه ساعت انتخاب کن');
                return;
            }

            let startAtInput = form.querySelector('input[name="start_at"]');
            if (startAtInput) startAtInput.value = this.startAt;

            let serviceInput = form.querySelector('input[name="service_id"]');
            if (serviceInput) serviceInput.value = this.selectedServiceId;

            let staffInput = form.querySelector('input[name="staff_id"]');
            if (staffInput) staffInput.value = this.selectedStaffId || '';

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