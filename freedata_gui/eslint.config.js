import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'

export default [
    ...pluginVue.configs['flat/base'],
    //...pluginVue.configs['flat/recommended'],
  {
    ignores: ["**/*.config.js", "!**/eslint.config.js", "**/src/locales/**", "**/node_modules/**", "**/dist/**"],
    rules: {
      'vue/no-unused-vars': 'error'
    },
    languageOptions: {
      //sourceType: 'module',
      globals: {
        ...globals.browser
      }
    }
  }
]