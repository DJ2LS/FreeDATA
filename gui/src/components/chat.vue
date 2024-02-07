<script setup lang="ts">
// @ts-nocheck
// disable typescript check beacuse of error with beacon histogram options

import chat_conversations from "./chat_conversations.vue";
import chat_messages from "./chat_messages.vue";
import chat_new_message from "./chat_new_message.vue";

import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

import { useChatStore } from "../store/chatStore.js";
const chat = useChatStore(pinia);

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
} from "chart.js";

import { Bar } from "vue-chartjs";
import { ref, computed } from "vue";
import annotationPlugin from "chartjs-plugin-annotation";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
  annotationPlugin,
);

var beaconHistogramOptions = {
  type: "bar",
  bezierCurve: false, //remove curves from your plot
  scaleShowLabels: false, //remove labels
  tooltipEvents: [], //remove trigger from tooltips so they will'nt be show
  pointDot: false, //remove the points markers
  scaleShowGridLines: true, //set to false to remove the grids background
  maintainAspectRatio: true,
  plugins: {
    legend: {
      display: false,
    },
    annotation: {
      annotations: [
        {
          type: "line",
          mode: "horizontal",
          scaleID: "y",
          value: 0,
          borderColor: "darkgrey", // Set the color to dark grey for the zero line
          borderWidth: 0.5, // Set the line width
        },
      ],
    },
  },

  scales: {
    x: {
      position: "bottom",
      display: false,
      min: -10,
      max: 15,
      ticks: {
        display: false,
      },
    },
    y: {
      display: false,
      min: -5,
      max: 10,
      ticks: {
        display: false,
      },
    },
  },
};

const beaconHistogramData = computed(() => ({
  labels: chat.beaconLabelArray,
  datasets: [
    {
      data: chat.beaconDataArray,
      tension: 0.1,
      borderColor: "rgb(0, 255, 0)",

      backgroundColor: function (context) {
        var value = context.dataset.data[context.dataIndex];
        return value >= 0 ? "green" : "red";
      },
    },
  ],
}));
</script>

<template>
  <div class="container-fluid m-0 p-0">
    <div class="row h-100 ms-0 mt-0 me-1">
      <div class="col-3 m-0 p-0 h-100 bg-light">
        <!------Chats area ---------------------------------------------------------------------->
        <div class="container-fluid vh-100 overflow-auto m-0 p-0">
          <chat_conversations />
        </div>
        <div class="h-100">
          <div
            class="list-group overflow-auto"
            id="list-tab-chat"
            role="tablist"
            style="height: calc(100vh - 70px)"
          ></div>
        </div>
      </div>
      <div class="col-9 border-start vh-100 p-0">
        <div class="d-flex flex-column vh-100">
          <!-- Top Navbar -->
          <nav class="navbar sticky-top bg-body-tertiary shadow">
            <div class="input-group mb-0 p-0 w-25">
              <button type="button" class="btn btn-outline-secondary" disabled>
                Beacons
              </button>

              <div
                class="form-floating border border-secondary-subtle border-1 rounded-end"
              >
                <Bar
                  :data="beaconHistogramData"
                  :options="beaconHistogramOptions"
                  width="300"
                  height="50"
                />
              </div>
            </div>
          </nav>

          <!-- Chat Messages Area -->
          <div class="flex-grow-1 overflow-auto">
            <chat_messages />
          </div>

          <chat_new_message />
        </div>

        <!------ new message area ---------------------------------------------------------------------->
      </div>
    </div>
  </div>

  <!-- user modal -->

  <div
    class="modal fade"
    id="userModal"
    tabindex="-1"
    aria-labelledby="userModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog" style="max-width: 600px">
      <div class="modal-content">
        <div class="card mb-1 border-0">
          <div class="row g-0">
            <div class="col-md-4">
              <div class="row position-relative p-0 m-0">
                <div class="col p-0 m-0">
                  <img
                    src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgZmlsbD0iY3VycmVudENvbG9yIiBjbGFzcz0iYmkgYmktcGVyc29uLWJvdW5kaW5nLWJveCIgdmlld0JveD0iMCAwIDE2IDE2Ij4KICA8cGF0aCBkPSJNMS41IDFhLjUuNSAwIDAgMC0uNS41djNhLjUuNSAwIDAgMS0xIDB2LTNBMS41IDEuNSAwIDAgMSAxLjUgMGgzYS41LjUgMCAwIDEgMCAxaC0zek0xMSAuNWEuNS41IDAgMCAxIC41LS41aDNBMS41IDEuNSAwIDAgMSAxNiAxLjV2M2EuNS41IDAgMCAxLTEgMHYtM2EuNS41IDAgMCAwLS41LS41aC0zYS41LjUgMCAwIDEtLjUtLjV6TS41IDExYS41LjUgMCAwIDEgLjUuNXYzYS41LjUgMCAwIDAgLjUuNWgzYS41LjUgMCAwIDEgMCAxaC0zQTEuNSAxLjUgMCAwIDEgMCAxNC41di0zYS41LjUgMCAwIDEgLjUtLjV6bTE1IDBhLjUuNSAwIDAgMSAuNS41djNhMS41IDEuNSAwIDAgMS0xLjUgMS41aC0zYS41LjUgMCAwIDEgMC0xaDNhLjUuNSAwIDAgMCAuNS0uNXYtM2EuNS41IDAgMCAxIC41LS41eiIvPgogIDxwYXRoIGQ9Ik0zIDE0cy0xIDAtMS0xIDEtNCA2LTQgNiAzIDYgNC0xIDEtMSAxSDN6bTgtOWEzIDMgMCAxIDEtNiAwIDMgMyAwIDAgMSA2IDB6Ii8+Cjwvc3ZnPg=="
                    class="img-fluid rounded-start w-100"
                    alt="..."
                    id="user_info_image"
                  />
                </div>
                <div
                  class="col position-absolute image-overlay text-white justify-content-center align-items-center d-flex align-middle h-100 opacity-0"
                  id="userImageSelector"
                >
                  <i class="bi bi-upload" style="font-size: 2.2rem"></i>
                </div>
              </div>
            </div>
            <div class="col-md-8">
              <div class="card-body">
                <div class="input-group input-group-sm mb-1">
                  <span class="input-group-text"
                    ><i class="bi bi-pass"></i
                  ></span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Callsign"
                    id="user_info_callsign"
                    aria-label="Call"
                    aria-describedby="basic-addon1"
                  />
                  <span class="input-group-text"
                    ><i class="bi bi-person-vcard"></i
                  ></span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="name"
                    id="user_info_name"
                    aria-label="Name"
                    aria-describedby="basic-addon1"
                  />
                  <span class="input-group-text"
                    ><i class="bi bi-sunrise"></i
                  ></span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="age"
                    id="user_info_age"
                    aria-label="age"
                    aria-describedby="basic-addon1"
                  />
                </div>

                <div class="input-group input-group-sm mb-1">
                  <span class="input-group-text"
                    ><i class="bi bi-house"></i
                  ></span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Location"
                    id="user_info_location"
                    aria-label="Name"
                    aria-describedby="basic-addon1"
                  />
                  <span class="input-group-text"
                    ><i class="bi bi-pin-map"></i
                  ></span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Grid"
                    id="user_info_gridsquare"
                    aria-label="Name"
                    aria-describedby="basic-addon1"
                  />
                </div>

                <div class="input-group input-group-sm mb-1">
                  <span class="input-group-text"
                    ><i class="bi bi-projector"></i
                  ></span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Radio"
                    id="user_info_radio"
                    aria-label="Name"
                    aria-describedby="basic-addon1"
                  />

                  <span class="input-group-text"
                    ><i class="bi bi-broadcast-pin"></i
                  ></span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Antenna"
                    id="user_info_antenna"
                    aria-label="Name"
                    aria-describedby="basic-addon1"
                  />
                </div>

                <div class="input-group input-group-sm mb-1">
                  <span class="input-group-text"
                    ><i class="bi bi-envelope"></i
                  ></span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Email"
                    id="user_info_email"
                    aria-label="Name"
                    aria-describedby="basic-addon1"
                  />

                  <span class="input-group-text"
                    ><i class="bi bi-globe"></i
                  ></span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Website"
                    id="user_info_website"
                    aria-label="Name"
                    aria-describedby="basic-addon1"
                  />
                </div>
                <div class="input-group input-group-sm mb-1">
                  <span class="input-group-text"
                    ><i class="bi bi-info-circle"></i
                  ></span>
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Comments"
                    id="user_info_comments"
                    aria-label="Comments"
                    aria-describedby="basic-addon1"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <button
          type="button"
          class="btn btn-primary"
          data-bs-dismiss="modal"
          aria-label="Close"
          id="userInfoSave"
        >
          Save & Close
        </button>
      </div>
    </div>
  </div>
  <!-- dx user modal -->
  <div
    class="modal fade"
    id="userModalDX"
    tabindex="-1"
    aria-labelledby="userModalDXLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog" style="max-width: 600px">
      <div class="modal-content">
        <div class="card mb-1 border-0">
          <div class="row g-0">
            <div class="col-md-4">
              <img
                src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiIgZmlsbD0iY3VycmVudENvbG9yIiBjbGFzcz0iYmkgYmktcGVyc29uLWJvdW5kaW5nLWJveCIgdmlld0JveD0iMCAwIDE2IDE2Ij4KICA8cGF0aCBkPSJNMS41IDFhLjUuNSAwIDAgMC0uNS41djNhLjUuNSAwIDAgMS0xIDB2LTNBMS41IDEuNSAwIDAgMSAxLjUgMGgzYS41LjUgMCAwIDEgMCAxaC0zek0xMSAuNWEuNS41IDAgMCAxIC41LS41aDNBMS41IDEuNSAwIDAgMSAxNiAxLjV2M2EuNS41IDAgMCAxLTEgMHYtM2EuNS41IDAgMCAwLS41LS41aC0zYS41LjUgMCAwIDEtLjUtLjV6TS41IDExYS41LjUgMCAwIDEgLjUuNXYzYS41LjUgMCAwIDAgLjUuNWgzYS41LjUgMCAwIDEgMCAxaC0zQTEuNSAxLjUgMCAwIDEgMCAxNC41di0zYS41LjUgMCAwIDEgLjUtLjV6bTE1IDBhLjUuNSAwIDAgMSAuNS41djNhMS41IDEuNSAwIDAgMS0xLjUgMS41aC0zYS41LjUgMCAwIDEgMC0xaDNhLjUuNSAwIDAgMCAuNS0uNXYtM2EuNS41IDAgMCAxIC41LS41eiIvPgogIDxwYXRoIGQ9Ik0zIDE0cy0xIDAtMS0xIDEtNCA2LTQgNiAzIDYgNC0xIDEtMSAxSDN6bTgtOWEzIDMgMCAxIDEtNiAwIDMgMyAwIDAgMSA2IDB6Ii8+Cjwvc3ZnPg=="
                class="img-fluid rounded-start w-100"
                alt="..."
                id="dx_user_info_image"
              />
            </div>
            <div class="col-md-8">
              <div class="card-body">
                <h5>
                  <span
                    class="badge bg-secondary"
                    id="dx_user_info_callsign"
                  ></span>
                  -
                  <span
                    class="badge bg-secondary"
                    id="dx_user_info_name"
                  ></span>
                  <span class="badge bg-secondary" id="dx_user_info_age"></span>
                </h5>

                <ul class="card-text list-unstyled">
                  <li>
                    <strong class="col"><i class="bi bi-house"></i> </strong
                    ><span id="dx_user_info_location"></span> (<span
                      id="dx_user_info_gridsquare"
                    ></span
                    >)
                  </li>
                  <li>
                    <strong class="col"><i class="bi bi-envelope"></i> </strong
                    ><span id="dx_user_info_email"></span>
                  </li>
                  <li>
                    <strong class="col"><i class="bi bi-globe"></i> </strong
                    ><span id="dx_user_info_website"></span>
                  </li>
                  <li>
                    <strong class="col"
                      ><i class="bi bi-broadcast-pin"></i> </strong
                    ><span id="dx_user_info_antenna"></span>
                  </li>
                  <li>
                    <strong class="col"><i class="bi bi-projector"></i> </strong
                    ><span id="dx_user_info_radio"></span>
                  </li>
                  <li>
                    <strong class="col"
                      ><i class="bi bi-info-circle"></i> </strong
                    ><span id="dx_user_info_comments"></span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div class="input-group input-group-sm m-0 p-0">
          <button
            type="button"
            class="btn btn-warning w-75"
            aria-label="Request"
            id="requestUserInfo"
          >
            Request user data (about 20kBytes!)
          </button>

          <button
            type="button"
            class="btn btn-primary w-25"
            data-bs-dismiss="modal"
            aria-label="Close"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- user shared folder -->
  <div
    class="modal fade"
    id="sharedFolderModal"
    tabindex="-1"
    aria-labelledby="sharedFolderModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="sharedFolderModalLabel">
            My Shared folder
            <button
              type="button"
              class="btn btn-primary"
              id="openSharedFilesFolder"
            >
              <i class="bi bi-archive"></i>
            </button>
          </h1>

          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>

        <div class="modal-body">
          <div class="container-fluid p-0">
            <div class="center mb-1">
              <div class="badge text-bg-info">
                <i class="bi bi-info"></i> Change folder in settings!
              </div>
            </div>
            <div class="table-responsive">
              <!-- START OF TABLE FOR SHARED FOLDER -->
              <table
                class="table table-sm table-hover table-bordered align-middle"
              >
                <thead>
                  <tr>
                    <th scope="col">#</th>
                    <th scope="col">Name</th>
                    <th scope="col">Type</th>
                    <th scope="col">Size</th>
                  </tr>
                </thead>
                <tbody id="sharedFolderTable"></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- HELP MODAL -->
  <div
    class="modal fade"
    data-bs-backdrop="static"
    tabindex="-1"
    id="chatHelpModal"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Chat Help</h5>
          <button
            type="button"
            class="btn btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="card mb-3">
            <div class="card-body">
              <p class="card-text">
                Welcome to the chat window. Heard stations are listed in the
                list on the left. Clicking on a station will show messages sent
                and/or received from the selected station. Additional help is
                available on various extra features below.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <button type="button" class="btn btn-sm btn-primary ms-2">
                <i class="bi bi-person" style="font-size: 1.2rem"></i>
              </button>
              <p class="card-text">
                Set your station information and picture. This information can
                be requested by a remote station and can be enabled/disabled via
                settings.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary ms-2"
              >
                <i class="bi bi-person" style="font-size: 1.2rem"></i>
              </button>
              <p class="card-text">
                Request the selected station's information.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <button
                type="button"
                class="btn btn-sm btn-outline-secondary ms-2"
              >
                <i class="bi bi-files" style="font-size: 1.2rem"></i>
              </button>
              <p class="card-text">
                Request the selected station's shared file(s) list. Clicking
                <button type="button" class="btn btn-sm btn-primary ms-2">
                  <i class="bi bi-files" style="font-size: 1.2rem"></i>
                </button>
                will allow you to preview your shared files. Shared file can be
                enabled/disabled in settings.
              </p>
            </div>
          </div>
          <div class="card mb-3">
            <div class="card-body">
              <button
                type="button"
                class="btn btn-small btn-outline-primary dropdown-toggle me-2"
              >
                <i class="bi bi-funnel-fill"></i>
              </button>
              <p class="card-text">
                The filter button allows you to show or hide certain types of
                messages. A lot of data is logged and this allows you to modify
                what is shown. By default sent and received messages and ping
                acknowlegements are displayed.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <!-- dx user shared folder -->
  <div
    class="modal fade"
    id="sharedFolderModalDX"
    tabindex="-1"
    aria-labelledby="sharedFolderModalDXLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog modal-dialog-scrollable">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="sharedFolderModalDXLabel">
            Shared folder
          </h1>
          <button
            type="button"
            class="btn btn-primary m-2"
            aria-label="Request"
            id="requestSharedFolderList"
          >
            <i class="bi bi-arrow-repeat"></i>
          </button>

          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div class="container-fluid">
            <div class="table-responsive">
              <!-- START OF TABLE FOR SHARED FOLDER DX -->
              <table
                class="table table-sm table-hover table-bordered align-middle"
              >
                <thead>
                  <tr>
                    <th scope="col">#</th>
                    <th scope="col">Name</th>
                    <th scope="col">Type</th>
                    <th scope="col">Size</th>
                  </tr>
                </thead>
                <tbody id="sharedFolderTableDX"></tbody>
              </table>
            </div>
          </div>
          <div class="modal-footer">
            <div class="input-group input-group-sm m-0 p-0"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
