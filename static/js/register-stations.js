/**
 * Alpine.js component برای صفحه‌ی ایستگاه‌های سالن (register).
 *
 * ─── استفاده: ───
 *   <div x-data="stationsForm()">
 */

function stationsForm() {
    return {
        stations: [{ name: '', staff: '' }],

        addStation() {
            this.stations.push({ name: '', staff: '' });
        },

        removeStation(index) {
            if (this.stations.length > 1) {
                this.stations.splice(index, 1);
            }
        },
    };
}