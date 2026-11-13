/** Tailwind (standalone CLI): ./bin/tailwindcss -i static/css/src/app.css -o static/css/app.css --minify */
module.exports = {
  content: ['./templates/**/*.html', './apps/**/templates/**/*.html', './static/js/**/*.js', './apps/**/editor_spec.py'],
  theme: {
    extend: {
      colors: {
        bg: '#f3f4f1', panel: '#ffffff', ink: '#1c1f1d', muted: '#5f655f', line: '#e3e5e0',
        accent: { DEFAULT: '#1f6f4a', soft: '#e6f2ec', dark: '#185a3c' }, danger: '#a83a29',
      },
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Arial', 'sans-serif'] },
    },
  },
  plugins: [],
};
