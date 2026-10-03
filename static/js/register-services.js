/**
 * Alpine.js component برای صفحه‌ی خدمات (register).
 *
 * ─── استفاده: ───
 *   <div x-data="servicesForm()">
 */

function servicesForm() {
    return {
        services: [{ name: '', duration: 30, price: '' }],

        addService() {
            this.services.push({ name: '', duration: 30, price: '' });
        },

        removeService(index) {
            if (this.services.length > 1) {
                this.services.splice(index, 1);
            }
        },
    };
}