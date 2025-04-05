import i18next from "i18next";

// Function to load translation JSON files from the locales folder.
// It expects file names like "en_english.json" or "de_deutsch.json"
function loadLocaleMessages() {
  // Automatically load all JSON files in ../locales
  const locales = require.context(
    "../locales",
    true,
    /[A-Za-z0-9-_,\s]+\.json$/i,
  );
  const resources = {};
  const availableLanguages = [];

  locales.keys().forEach((key) => {
    // Use regex to extract the ISO code and language name from the file name.
    // For example, "./en_english.json" extracts iso: "en", name: "english"
    const matched = key.match(/\.\/([^_]+)_([^.]+)\.json$/i);
    if (matched && matched.length > 2) {
      const iso = matched[1];
      const name = matched[2];
      // Load the translation JSON file
      const translations = locales(key);
      // Wrap translations into the default namespace ("translation")
      resources[iso] = { translation: translations };
      availableLanguages.push({ iso, name });
    }
  });

  return { resources, availableLanguages };
}

const { resources, availableLanguages } = loadLocaleMessages();

i18next.init(
  {
    lng: "en",
    fallbackLng: "en",
    resources,
  },
  (err) => {
    if (err) {
      console.error("i18next initialization error:", err);
    } else {
      console.log("i18next is ready.");
    }
  },
);

export default i18next;
export { availableLanguages };
