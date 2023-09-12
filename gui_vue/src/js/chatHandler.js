const path = require("path");
const fs = require("fs");

// pinia store setup
import { setActivePinia } from 'pinia';
import pinia from '../store/index';
setActivePinia(pinia);

import { useChatStore } from '../store/chatStore.js';
const chat = useChatStore(pinia);


// ---- MessageDB
try {
  var PouchDB = require("pouchdb");
} catch (err) {
  console.log(err);

  /*
    This is a fix for raspberryPi where we get an error when loading pouchdb because of
    leveldown package isnt running on ARM devices.
    pouchdb-browser does not depend on leveldb and seems to be working.
    */
  console.log("using pouchdb-browser fallback");
  var PouchDB = require("pouchdb-browser");
}


PouchDB.plugin(require("pouchdb-find"));
//PouchDB.plugin(require('pouchdb-replication'));
PouchDB.plugin(require("pouchdb-upsert"));



// https://stackoverflow.com/a/26227660
var appDataFolder =
  process.env.APPDATA ||
  (process.platform == "darwin"
    ? process.env.HOME + "/Library/Application Support"
    : process.env.HOME + "/.config");
var configFolder = path.join(appDataFolder, "FreeDATA");




var chatDB = path.join(configFolder, "chatDB");
var db = new PouchDB(chatDB);

/* -------- CREATE DATABASE INDEXES */
createChatIndex();







chat.callsign_list = new Set()






export async function updateAllChat() {

  //Ensure we create an index before running db.find
  //We can't rely on the default index existing before we get here...... :'(
  await db
    .createIndex({
      index: {
        fields: [{ dxcallsign: "asc" }, { timestamp: "asc" }],
      },
    })
    .then(async function (result) {
      // handle result
      await db
        .find({
          selector: {
            $and: [
              { dxcallsign: { $exists: true } },
              { timestamp: { $exists: true } },
              { $or: chat.chat_filter },
            ],
            //$or: chat.chat_filter
          },
          sort: [{ dxcallsign: "asc" }, { timestamp: "asc" }],
        })
        .then(async function (result) {
          console.log(result);
          for (var item of result.docs) {
           console.log(item)
            chat.callsign_list.add(item.dxcallsign)

          }

          // handle result async
        

          /*

          if (typeof result !== "undefined") {
            for (const item of result.docs) {
              //await otherwise history will not be in chronological order
              await db
                .get(item._id, {
                  attachments: true,
                })
                .then(function (item_with_attachments) {
                  update_chat(item_with_attachments);
                });
            }
          }
          */


        })
        .catch(function (err) {
          console.log(err);
        });
    })
    .catch(function (err) {
      console.log(err);
    });

}






function createChatIndex() {
  db.createIndex({
    index: {
      fields: [
        "timestamp",
        "uuid",
        "dxcallsign",
        "dxgrid",
        "msg",
        "checksum",
        "type",
        "command",
        "status",
        "percent",
        "attempt",
        "hmac_signed",
        "bytesperminute",
        "_attachments",
        "new",
      ],
    },
  })
    .then(function (result) {
      // handle result
      console.log(result);
    })
    .catch(function (err) {
      console.log(err);
    });
}
