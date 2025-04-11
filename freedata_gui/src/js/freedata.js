/**
 * Binary to ASCII replacement
 * @param {string} data in normal/usual utf-8 format
 * @returns base64 encoded string
 */
export function btoa_FD(data) {
  //exports.btoa_FD = function (data) {
  return Buffer.from(data, "utf-8").toString("base64");
}
/**
 * ASCII to Binary replacement
 * @param {string} data in base64 encoding
 * @returns utf-8 normal/usual string
 */
export function atob_FD(data) {
  //exports.atob_FD = function (data) {
  return Buffer.from(data, "base64").toString("utf-8");
}
/**
 * UTF8 to ASCII btoa
 * @param {string} data in base64 encoding
 * @returns base64 bota compatible data for use in browser
 */
export function atob(data) {
  //exports.atob = function (data) {
  return window.btoa(Buffer.from(data, "base64").toString("utf8"));
}
//https://medium.com/@asadise/sorting-a-json-array-according-one-property-in-javascript-18b1d22cd9e9
/**
 * Sort a json collection by a property ascending
 * @param {string} property property to sort on
 * @returns sorted json collection
 */
export function sortByProperty(property) {
  return function (a, b) {
    if (a[property] > b[property]) return 1;
    else if (a[property] < b[property]) return -1;

    return 0;
  };
}

//https://medium.com/@asadise/sorting-a-json-array-according-one-property-in-javascript-18b1d22cd9e9
/**
 * Sort a json collection by a property descending
 * @param {string} property property to sort on
 * @returns sorted json collection
 */
export function sortByPropertyDesc(property) {
  return function (a, b) {
    if (a[property] < b[property]) return 1;
    else if (a[property] > b[property]) return -1;

    return 0;
  };
}

/**
 * Validate a call sign with SSID
 * @param {string} callsign callsign to check
 * @returns true or false if callsign appears to be valid with an SSID
 */
export function validateCallsignWithSSID(callsign) {
  const patt = new RegExp("^[A-Za-z0-9]{1,7}-[0-9]{1,3}$");
  if (!callsign || !patt.test(callsign)) {
    console.error(
      `Call sign given is not in correct format or missing; callsign passed is: ${callsign}`,
    );
    return false;
  }
  return true;
}

/**
 * Validate a call sign without SSID
 * @param {string} callsign callsign to check
 * @returns true or false if callsign appears to be valid without an SSID
 */
export function validateCallsignWithoutSSID(callsign) {
  const patt = new RegExp("^[A-Za-z0-9]{1,7}$");
  if (!callsign || !patt.test(callsign)) {
    console.error(
      `Call sign given is not in correct format or missing; callsign passed is: ${callsign}`,
    );
    return false;
  }
  return true;
}

/**
 * Get application data path based on the environment.
 * In a browser environment, this function now returns a fixed path or directory name.
 * @returns {string} path for storage
 */
export function getAppDataPath() {
  // For browser environments, return the fixed path or directory name "FreeDATA".
  return "FreeDATA"; // Adjust this value as needed for your application.
}

/**
 * Retrieve data from localStorage.
 * @param {string} key - The key of the data to retrieve.
 * @returns {string|null} The retrieved value or null if not found.
 */
export function getFromLocalStorage(key) {
  try {
    return localStorage.getItem(key);
  } catch (error) {
    console.error("Failed to retrieve data from localStorage:", error);
    return null;
  }
}

/**
 * Remove data from localStorage.
 * @param {string} key - The key of the data to remove.
 */
export function removeFromLocalStorage(key) {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error("Failed to remove data from localStorage:", error);
  }
}

/**
 * Set GUI Color Mode.
 * @param {string} colorMOde - The colormode, light, dark, auto.
 */
export function applyColorMode(colorMode) {
  // If set to "auto", detect the OS preference using matchMedia

  console.log(colorMode);
  if (colorMode === "auto") {
    colorMode =
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
  }
  // If it's an empty string, default to "light"
  else if (colorMode === "") {
    colorMode = "light";
  }

  // Apply the theme by setting the attribute on the document element
  document.documentElement.setAttribute("data-bs-theme", colorMode);
}
