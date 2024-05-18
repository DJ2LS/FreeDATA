const { notarize } = require('@electron/notarize');

async function notarizing(context) {
  const { electronPlatformName, appOutDir } = context;
    console.log("Notarization...")
  if (electronPlatformName !== 'darwin') {
  console.log("--> Platform:" + electronPlatformName + " detected: not a APPLE system. Skipping")
    return;
  }

  console.log("--> Platform:" + electronPlatformName + " detected: Trying to notarize app.")
  const appName = context.packager.appInfo.productFilename;

  return await notarize({
    tool: 'notarytool',
    appBundleId: 'app.freedata',
    appPath: `${appOutDir}/${appName}.app`,
    appleId: process.env.APPLE_ID,
    appleIdPassword: process.env.APPLE_ID_PASSWORD,
    teamId: process.env.APPLE_TEAM_ID
  });
}

exports.default = notarizing;
