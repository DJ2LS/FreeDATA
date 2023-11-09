let socket;
let retries = 0;
let maxRetries = 15;

function connect() {

    socket = new WebSocket("ws://localhost:5000/events");

    // handle opening
    socket.addEventListener('open', function (event) {
        console.log('Connected to the WebSocket server');
        retries = 0; // Reset the retries back to 0 since the connection was successful
    });

    // handle data
    socket.addEventListener('message', function (event) {
        console.log('Message from server:', event.data);
    });

    // handle errors
    socket.addEventListener('error', function (event) {
        console.error('WebSocket error:', event);
    });

    // handle closing and reconnect
    socket.addEventListener('close', function (event) {
        console.log('WebSocket connection closed:', event.code);

        // Reconnect handler
        if (!event.wasClean && retries < maxRetries) {
            setTimeout(() => {
                console.log("Reconnecting to websocket. Attempt: " + retries)
                connect();
            }, 1000);
            retries++;
        }
    });
}

// Initial connection attempt
connect();
