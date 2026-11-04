const path = require('path');

// Absolute path so Tailwind resolves its config even when Next is started from the repo root.
module.exports = {
  plugins: {
    tailwindcss: { config: path.join(__dirname, 'tailwind.config.js') },
    autoprefixer: {},
  },
};
