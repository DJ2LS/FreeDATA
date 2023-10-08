const fs = require("fs");

/**
 * Binary to ASCII replacement
 * @param {string} data in normal/usual utf-8 format
 * @returns base64 encoded string
 */
export function btoa_FD(data) {
//exports.btoa_FD = function (data) {
  return Buffer.from(data, "utf-8").toString("base64");
};
/**
 * ASCII to Binary replacement
 * @param {string} data in base64 encoding
 * @returns utf-8 normal/usual string
 */
export function atob_FD(data) {
//exports.atob_FD = function (data) {
  return Buffer.from(data, "base64").toString("utf-8");
};
/**
 * UTF8 to ASCII btoa
 * @param {string} data in base64 encoding
 * @returns base64 bota compatible data for use in browser
 */
export function atob(data) {
//exports.atob = function (data) {
  return window.btoa(Buffer.from(data, "base64").toString("utf8"));
};
