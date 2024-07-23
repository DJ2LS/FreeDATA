import { v4 as uuidv4 } from 'uuid';
import * as bootstrap from 'bootstrap';

export function displayToast(type, icon, content, duration) {
  const mainToastContainer = document.getElementById('mainToastContainer');

  const randomID = uuidv4();
  const toastCode = `
    <div class="toast align-items-center bg-outline-${type} border-1" id="${randomID}" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body p-0 m-0 bg-white rounded-2 w-100">
          <div class="row p-1 m-0">
            <div class="col-auto bg-${type} rounded-start rounded-2 d-flex align-items-center">
              <i class="bi ${icon}" style="font-size: 1rem; color: white;"></i>
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

  // Insert toast to toast container
  mainToastContainer.insertAdjacentHTML('beforeend', toastCode);

  // Register toast
  const toastHTMLElement = document.getElementById(randomID);
  const toast = bootstrap.Toast.getOrCreateInstance(toastHTMLElement); // Returns a Bootstrap toast instance
  toast._config.delay = duration;

  // Show toast
  toast.show();

  // Register event listener to remove toast when hidden
  toastHTMLElement.addEventListener('hidden.bs.toast', function handleToastHidden() {
    toastHTMLElement.removeEventListener('hidden.bs.toast', handleToastHidden);
    toastHTMLElement.remove();
  });
}
