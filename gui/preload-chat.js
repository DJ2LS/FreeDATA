const path = require('path')
const {
    ipcRenderer
} = require('electron')

const { v4: uuidv4 } = require('uuid');

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
var db = new PouchDB(chatDB);



// get all messages from database
//var messages = db.get("messages").value()

// get all dxcallsigns in database



var dxcallsigns = new Set();

db.allDocs({
  include_docs: true,
  attachments: true
}).then(function (result) {
  // handle result
  // get all dxcallsigns and append to list
  result.rows.forEach(function(item) {
    update_chat(item.doc)
  });
    
}).catch(function (err) {
  console.log(err);
});



// WINDOW LISTENER
window.addEventListener('DOMContentLoaded', () => {




    // SEND MSG
    document.getElementById("sendMessage").addEventListener("click", () => {
            var dxcallsign = document.getElementById('chatModuleDxCall').value
            dxcallsign = dxcallsign.toUpperCase()
            message = document.getElementById('chatModuleMessage').value
            console.log(dxcallsign)
            let Data = {
                command: "send_message",
                dxcallsign : dxcallsign, 
                mode : 255, 
                frames : 1, 
                data : message, 
                checksum : '123'
            };
            ipcRenderer.send('run-tnc-command', Data);
            
            
        var uuid = uuidv4();
        db.post({
          _id: uuid,
          timestamp: Math.floor(Date.now() / 1000),
          dxcallsign: dxcallsign,
          dxgrid: 'NULL',
          msg: message,
          checksum: 'NULL',
          type: "transmit"
        }).then(function (response) {
          // handle response
          console.log("new database entry")
          console.log(response)
     
        }).catch(function (err) {
          console.log(err);
        });




        db.get(uuid).then(function (doc) {
          // handle doc
          update_chat(doc)
        }).catch(function (err) {
          console.log(err);
        });        
            
            
            
            
            
                
    })






});

ipcRenderer.on('action-new-msg-received', (event, arg) => {
    //console.log(arg.data)
    
    var new_msg = arg.data
    new_msg.forEach(function(item) {
        //console.log(item)
    //for (i = 0; i < arg.data.length; i++) {
        
        let obj = new Object();
        
        var encoded_data = atob(item.data);
        var splitted_data = encoded_data.split(split_char)

        //obj.uuid = item.uuid;
        item.checksum = splitted_data[2]
        item.msg = splitted_data[3]
        //obj.dxcallsign = item.dxcallsign;
        //obj.dxgrid = item.dxgrid;
        //obj.timestamp = item.timestamp;
     
        





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
          dxcallsign: item.dxcallsign,
          dxgrid: item.dxgrid,
          msg: item.msg,
          checksum: item.checksum,
          type: "received"
        }).then(function (response) {
          // handle response
          console.log("new database entry")
          console.log(response)
     
        }).catch(function (err) {
          console.log(err);
        });




        db.get(item.uuid).then(function (doc) {
          // handle doc
          update_chat(doc)
        }).catch(function (err) {
          console.log(err);
        });






        
        
        
       
        
        
    });
    

      
      
      
      

});








// Update chat list
update_chat = function(obj) {

        var dxcallsign = obj.dxcallsign;
    
    // CALLSIGN LIST
    if(!(document.getElementById('chat-' + dxcallsign + '-list'))){
        var new_callsign = `
            <a class="list-group-item list-group-item-action" id="chat-${dxcallsign}-list" data-bs-toggle="list" href="#chat-${dxcallsign}" role="tab" aria-controls="chat-${dxcallsign}">
                      <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">${dxcallsign}</h5>
                        <!--<small>3 days ago</small>-->
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
            });   
        
    }
    
    
    // APPEND MESSAGES TO CALLSIGN

    var timestamp = dateFormat.format(obj.timestamp * 1000);
    
    if(!(document.getElementById('msg-' + obj._id))){
        if (obj.type == 'received'){
            var new_message = `
                <div class="card border-light mb-3 w-75" id="msg-${obj._id}">
                  <div class="card-body">
                    <p class="text-small mb-0 text-muted text-break">${timestamp}</p>
                    <p class="card-text">${obj.msg}</p>
                  </div>
                </div>
                `;
        }
        
        if (obj.type == 'transmit'){


            var new_message = `
                <div class="card text-right border-primary ml-auto mb-3 w-75" style="margin-left: auto;"id="msg-${obj._id}">
                  <div class="card-body">
                    <p class="text-small mb-0 text-muted text-break">${timestamp}</p>
                    <p class="card-text">${obj.msg}</p>
                  </div>
                </div>
                `;                
        }        
        
        
        
        
        
        
        

    var id = "chat-" + obj.dxcallsign
    document.getElementById(id).insertAdjacentHTML("beforeend", new_message);
    }
    
    
    
    
    
}
