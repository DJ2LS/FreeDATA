const { v4: uuidv4 } = require("uuid");
import * as bootstrap from "bootstrap";

export function displayToast(type, icon, content, duration) {
  let mainToastContainer = document.getElementById("mainToastContainer");

  let randomID = uuidv4();
  let toastCode = `
        <div class="toast align-items-center bg-outline-${type} border-1" id="${randomID}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body p-0 m-0 bg-white rounded-2 w-100">
                      <div class="row p-1 m-0">
                        <div class="col-auto bg-${type} rounded-start rounded-2 d-flex align-items-center">
                            <i class="bi ${icon}" style="font-size: 1rem; color: white"></i>
                        </div>
                        <div class="col p-2">
                          ${content}
                        </div>
                      </div>
                </div>
                <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

  // insert toast to toast container
  mainToastContainer.insertAdjacentHTML("beforeend", toastCode);

  // register toast
  let toastHTMLElement = document.getElementById(randomID);
  let toast = bootstrap.Toast.getOrCreateInstance(toastHTMLElement); // Returns a Bootstrap toast instance
  toast._config.delay = duration;

  // show toast
  toast.show();

  //register event listener if toast is hidden
  toastHTMLElement.addEventListener("hidden.bs.toast", () => {
    // remove eventListener
    toastHTMLElement.removeEventListener("hidden.bs.toast", this);
    // remove toast
    toastHTMLElement.remove();
  });
}
