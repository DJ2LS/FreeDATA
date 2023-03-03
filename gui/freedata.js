const fs = require("fs");
const { ipcRenderer } = require("electron");

/**
 * Save config and update config setting globally
 * @param {string} config - config data 
 * @param {string} configPath 
 */
exports.saveConfig = function (config, configPath){
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    ipcRenderer.send("set-config-global", config);
}

/**
 * Binary to ASCII replacement
 * @param {string} data in normal/usual utf-8 format
 * @returns base64 encoded string
 */
exports.btoa_FD = function (data) {
    return Buffer.from(data, "utf-8").toString("base64");
  }
  /**
   * ASCII to Binary replacement
   * @param {string} data in base64 encoding
   * @returns utf-8 normal/usual string
   */
 exports.atob_FD = function (data) {
    return Buffer.from(data, "base64").toString("utf-8");
  }
  /**
   * UTF8 to ASCII btoa
   * @param {string} data in base64 encoding
   * @returns base64 bota compatible data for use in browser
   */
exports.atob = function (data) {
    return window.btoa(Buffer.from(data, "base64").toString("utf8"));
  }