import { createI18n } from 'vue-i18n'

// Dynamically import all JSON files from the locales folder
function loadLocaleMessages() {
  const locales = require.context('../locales', true, /[A-Za-z0-9-_,\s]+\.json$/i)
  const messages = {}
  const languages = []
  locales.keys().forEach(key => {
    // Expecting file names like "./en_english.json" or "./de_deutsch.json"
    const matched = key.match(/\.\/([^_]+)_([^.]+)\.json$/i)
    if (matched && matched.length > 2) {
      const iso = matched[1]
      const name = matched[2]
      messages[iso] = locales(key)
      languages.push({ iso, name })
    }
  })
  return { messages, languages }
}

const { messages, languages } = loadLocaleMessages()

const i18n = createI18n({
  locale: 'de',
  fallbackLocale: 'en', // Fallback language (English)
  messages,
})

export default i18n
export const availableLanguages = languages
