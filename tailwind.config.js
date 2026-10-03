/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './templates/**/*.html',
        './apps/**/templates/**/*.html',
        './apps/**/*.py',
        './static/js/**/*.js',
    ],
    theme: {
        extend: {
            colors: {
                primary: '#2C3E50',
                accent:  '#B08D57',
                cream:   '#F5F0EB',
                darktext:'#1A1A1A',
                success: '#22C55E',
                warning: '#EAB308',
                danger:  '#EF4444',
            },
            fontFamily: {
                vazir: ['Vazirmatn', 'sans-serif'],
            },
        },
    },
    plugins: [],
}