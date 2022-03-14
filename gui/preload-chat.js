const path = require('path')
const {
    ipcRenderer
} = require('electron')

const { v4: uuidv4 } = require('uuid');
const utf8 = require('utf8');

// https://stackoverflow.com/a/26227660
var appDataFolder = process.env.APPDATA || (process.platform == 'darwin' ? process.env.HOME + '/Library/Application Support' : process.env.HOME + "/.config")
var configFolder = path.join(appDataFolder, "FreeDATA");
var configPath = path.join(configFolder, 'config.json')
const config = require(configPath);


// set date format
const dateFormat = new Intl.DateTimeFormat('en-GB', {
    timeStyle: 'long',
    dateStyle: 'full'
});

// split character
const split_char = '\0;'


var chatDB = path.join(configFolder, 'chatDB')

// ---- MessageDB
var PouchDB = require('pouchdb');
PouchDB.plugin(require('pouchdb-find'));
var db = new PouchDB(chatDB);



// get all messages from database
//var messages = db.get("messages").value()

// get all dxcallsigns in database





var dxcallsigns = new Set();






db.createIndex({
  index: {
    fields: ['timestamp', 'uuid', 'dxcallsign', 'dxgrid', 'msg', 'checksum', 'type', 'command', 'status']
  }
}).then(function (result) {
  // handle result
  console.log(result)
}).catch(function (err) {
  console.log(err);
});


          
db.find({
          selector: {
            timestamp: {$exists: true}},
          sort: [{'timestamp': 'asc'}]
        }).then(function (result) {
  // handle result
  console.log(result);
  console.log(typeof(result));
  if(typeof(result) !== 'undefined'){
  result.docs.forEach(function(item) {
 
    update_chat(item);
  
    });
    
    }
}).catch(function (err) {
  console.log(err);
});
  
  

// WINDOW LISTENER
window.addEventListener('DOMContentLoaded', () => {

 
    document.querySelector('emoji-picker').addEventListener("emoji-click", (event) => {  
  document.getElementById('chatModuleMessage').setRangeText(event.detail.emoji.unicode)
  
  
  console.log(event.detail);
})
  
  
  
document.getElementById("emojipickerbutton").addEventListener("click", () => {  
var element = document.getElementById("emojipickercontainer")

    console.log(element.style.display);
    
    
  if (element.style.display === "none") {
    element.style.display = "block";
  } else {
    element.style.display = "none";
  }




})


    // SEND MSG
    document.getElementById("sendMessage").addEventListener("click", () => {
            document.getElementById('emojipickercontainer').style.display = "none";
            var dxcallsign = document.getElementById('chatModuleDxCall').value;
            dxcallsign = dxcallsign.toUpperCase();
            
            var chatmessage = document.getElementById('chatModuleMessage').value;
            //chatmessage = Buffer.from(chatmessage, 'utf-8').toString();

            
            
            var uuid = uuidv4();
            console.log(chatmessage)
            let Data = {
                command: "send_message",
                dxcallsign : dxcallsign, 
                mode : 255, 
                frames : 1, 
                data : chatmessage, 
                checksum : '123',
                uuid : uuid
            };
            ipcRenderer.send('run-tnc-command', Data);
            
            
        
        db.post({
          _id: uuid,
          timestamp: Math.floor(Date.now() / 1000),
          dxcallsign: dxcallsign,
          dxgrid: 'NULL',
          msg: chatmessage,
          checksum: 'NULL',
          type: "transmit",
          status: 'transmit',
          uuid: uuid
        }).then(function (response) {
          // handle response
          console.log("new database entry");
          console.log(response);
     
        }).catch(function (err) {
          console.log(err);
        });




        db.get(uuid).then(function (doc) {
          // handle doc
          update_chat(doc)
        }).catch(function (err) {
          console.log(err);
        });        
            
        // scroll to bottom    
        var element = document.getElementById("message-container");
        element.scrollTo(0,element.scrollHeight);   
        
        // clear input
        document.getElementById('chatModuleMessage').value = ''  
         
                
    })


});



ipcRenderer.on('action-update-transmission-status', (event, arg) => {

    console.log(arg.status);
    console.log(arg.uuid);


db.get(arg.uuid).then(function(doc) {

  return db.put({
    _id: arg.uuid,
    _rev: doc._rev,
      timestamp: doc.timestamp,
      dxcallsign: doc.dxcallsign,
      dxgrid: doc.dxgrid,
      msg: doc.msg,
      checksum: doc.checksum,
      type: "transmit",
      status: arg.status,
      uuid: doc.uuid
  });
}).then(function(response) {
  // handle response
          db.get(arg.uuid).then(function (doc) {
          // handle doc
          update_chat(doc);
        }).catch(function (err) {
          console.log(err);
        });  
}).catch(function (err) {
  console.log(err);
});

    
    
    
    

});

ipcRenderer.on('action-new-msg-received', (event, arg) => {
    console.log(arg);
    console.log(arg.data);
    
    var new_msg = arg.data;
    
    new_msg.forEach(function(item) {
        console.log(item);
    //for (i = 0; i < arg.data.length; i++) {
        
        let obj = new Object();
        
        var encoded_data = atob(item.data);
        var splitted_data = encoded_data.split(split_char);
        console.log(utf8.decode(splitted_data[3]));
        //obj.uuid = item.uuid;
        item.command = splitted_data[1];
        item.checksum = splitted_data[2];
        // convert message to unicode from utf8 because of emojis
        item.uuid = utf8.decode(splitted_data[3]);
        item.msg = utf8.decode(splitted_data[4]);
        //obj.dxcallsign = item.dxcallsign;
        //obj.dxgrid = item.dxgrid;
        //obj.timestamp = item.timestamp;
        item.status = 'null';


        // check if message not exists in database.
        // this might cause big cpu load of file is getting too big
        /*        
        if(!JSON.stringify(db.get("messages")).includes(item.uuid)){
            console.log("new message: " + item);
            db.get("messages").push(item).save();
        }
        */
        

        db.put({
          _id: item.uuid,
          timestamp: item.timestamp,
          uuid: item.uuid,
          dxcallsign: item.dxcallsign,
          dxgrid: item.dxgrid,
          msg: item.msg,
          checksum: item.checksum,
          type : "received",
          command : item.command,
          status : item.status
        }).then(function (response) {
          // handle response
          console.log("new database entry");
          console.log(response);
     
        }).catch(function (err) {
          console.log(err);
        });




        db.get(item.uuid).then(function (doc) {
          // handle doc
          
          // timestamp
          update_chat(doc);
        }).catch(function (err) {
          console.log(err);
        });

console.log("...................................")
return

    });

});


// Update chat list
update_chat = function(obj) {
        
console.log(obj);
        var dxcallsign = obj.dxcallsign;
        var timestamp = dateFormat.format(obj.timestamp * 1000);
        var dxgrid = obj.dxgrid;
    
    // CALLSIGN LIST
    if(!(document.getElementById('chat-' + dxcallsign + '-list'))){
        var new_callsign = `
            <a class="list-group-item list-group-item-action rounded-4 border-1 mb-2" id="chat-${dxcallsign}-list" data-bs-toggle="list" href="#chat-${dxcallsign}" role="tab" aria-controls="chat-${dxcallsign}">
                      <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">${dxcallsign}</h5>
                        <small>${dxgrid}</small>
                      </div>
                      <!--<p class="mb-1">JN48ea</p>-->
                  </a>

            `;
        document.getElementById('list-tab').insertAdjacentHTML("beforeend", new_callsign);
              
        var message_area = `
            <div class="tab-pane fade" id="chat-${dxcallsign}" role="tabpanel" aria-labelledby="chat-${dxcallsign}-list"></div>  
            `;
        document.getElementById('nav-tabContent').insertAdjacentHTML("beforeend", message_area); 
        
        // create eventlistener for listening on clicking on a callsign
        document.getElementById('chat-' + dxcallsign + '-list').addEventListener('click', function() {
            document.getElementById('chatModuleDxCall').value = dxcallsign;
            
            // scroll to bottom    
            var element = document.getElementById("message-container");
            element.scrollTo(0,element.scrollHeight);  
        
            });   
        
    }
    
 
    
    // APPEND MESSAGES TO CALLSIGN

            if (obj.status == 'transmit'){
                var message_class = 'card text-right border-primary bg-primary';
            }else if (obj.status == 'transmitting'){
                var message_class = 'card text-right border-warning bg-warning';
            }else if (obj.status == 'failed'){
                var message_class = 'card text-right border-danger bg-danger';
            }else if (obj.status == 'success'){
                var message_class = 'card text-right border-success bg-success';   
            } else {
                var message_class = 'card text-right border-secondary bg-secondary';
            }   
            
    
    if(!(document.getElementById('msg-' + obj._id))){
        if (obj.type == 'received'){
            var new_message = `
                    <div class="mt-3 mb-0 w-75" id="msg-${obj._id}">            
                    <p class="font-monospace text-small mb-0 text-muted text-break">${timestamp}</p>
                    <div class="card border-light bg-light" id="msg-${obj._id}">
                      <div class="card-body">
                        <p class="card-text text-break text-wrap">${obj.msg}</p>
                      </div>
                    </div>
                </div>
                `;
        }
        
        if (obj.type == 'transmit'){
        

            var new_message = `
                <div class="ml-auto mt-3 mb-0 w-75" style="margin-left: auto;">
                    <p class="font-monospace text-right mb-0 text-muted" style="text-align: right;">${timestamp}</p> 
                    <div class="${message_class}" id="msg-${obj._id}">
                      <div class="card-body">
                        <p class="card-text text-white text-break text-wrap">${obj.msg}</p>

                      </div>
                    </div>
                </div>
                `;                
        }    
        

    var id = "chat-" + obj.dxcallsign
    document.getElementById(id).insertAdjacentHTML("beforeend", new_message);
    var element = document.getElementById("message-container");
    element.scrollTo(0,element.scrollHeight);
    } else if(document.getElementById('msg-' + obj._id)) {
            id = "msg-" + obj._id;
            document.getElementById(id).className = message_class;
        }   
}


