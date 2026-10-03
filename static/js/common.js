/**
 * Alpine.js component های مشترک.
 *
 * ─── استفاده توی template: ───
 *   <div x-data="avatarPreview()">
 *   <div x-data="filePreview()">
 */

/**
 * پیش‌نمایش عکس قبل از آپلود.
 * برای فرم‌هایی که یه آواتار دارن.
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


/**
 * پیش‌نمایش اسم فایل (بدون عکس).
 * برای اسناد مثل پروانه کسب، عکس ورودی و...
 */
function filePreview() {
    return {
        fileName: '',

        handleFileChange(event) {
            const file = event.target.files[0];
            if (file) {
                this.fileName = file.name;
            }
        },
    };
}