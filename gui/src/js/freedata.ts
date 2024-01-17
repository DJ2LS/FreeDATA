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
 * Validate a call sign with ssid
 * @param {string} callsign callsign to check
 * @returns true or false if callsign appears to be valid with an SSID
 */
export function validateCallsignWithSSID(callsign: string) {
  var patt = new RegExp("^[A-Z]+[0-9][A-Z]*-(1[0-5]|[0-9])$");

  if (
    callsign === undefined ||
    callsign === "" ||
    patt.test(callsign) === false
  ) {
    console.error(
      "Call sign given is not in correct format or missing; callsign passed is:  " +
        callsign,
    );
    return false;
  }
  return true;
}
/**
 * Validate/check if a call sign has an SSID
 * @param {string} callsign callsign to check
 * @returns true or false if callsign appears to be valid without an SSID
 */
export function validateCallsignWithoutSSID(callsign: string) {
  var patt = new RegExp("^[A-Z]+[0-9][A-Z]+$");

  if (
    callsign === undefined ||
    callsign === "" ||
    patt.test(callsign) === false
  ) {
    console.error(
      "Call sign given is not in correct format or missing; callsign passed is:  " +
        callsign,
    );
    return false;
  }
  return true;
}
