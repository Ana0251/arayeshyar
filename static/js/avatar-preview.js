/**
 * Alpine.js component برای پیش‌نمایش آواتار.
 *
 * ─── استفاده: ───
 *   <div x-data="avatarPreview()">
 */

function avatarPreview() {
    return {
        previewUrl: null,
        fileName: '',

        handleFileChange(event) {
            const file = event.target.files[0];
            if (!file) return;

            this.fileName = '✓ ' + file.name;

            const reader = new FileReader();
            reader.onload = (e) => {
                this.previewUrl = e.target.result;
            };
            reader.readAsDataURL(file);
        },
    };
}