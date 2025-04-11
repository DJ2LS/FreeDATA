import pluginVue from "eslint-plugin-vue";
import globals from "globals";

export default [
  ...pluginVue.configs["flat/base"],
  //...pluginVue.configs['flat/recommended'],  // causes some errors not able to fix, yet. So disabled for now
  {
    ignores: [
      "**/*.config.js",
      "!**/eslint.config.js",
      "**/src/locales/**",
      "**/node_modules/**",
      "**/dist/**",
    ],
    rules: {
      "vue/no-unused-vars": "error",
      "vue/multi-word-component-names": "warn",
    },
    languageOptions: {
      //sourceType: 'module',
      globals: {
        ...globals.browser,
      },
    },
  },
];
