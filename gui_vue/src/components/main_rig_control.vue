<template>
<div class="card mb-0">
              <div class="card-header p-1">
                <div class="container">
                  <div class="row">
                    <div class="col-1">
                      <i class="bi bi-projector" style="font-size: 1.2rem"></i>
                    </div>
                    <div class="col-4">
                      <strong class="fs-5">Rig control</strong>
                    </div>
                    <div class="col-6">
                      <div
                        class="btn-group btn-group-sm"
                        role="group"
                        aria-label="radio-control-switch-disabled"
                      >
                        <input
                          type="radio"
                          class="btn-check"
                          name="radio-control-switch"
                          id="radio-control-switch-disabled"
                          autocomplete="off"
                        />
                        <label
                          class="btn btn-sm btn-outline-secondary"
                          for="radio-control-switch-disabled"
                        >
                          None / Vox
                        </label>

                        <div
                          class="btn-group btn-group-sm"
                          role="group"
                          aria-label="radio-control-switch-rigctld"
                        >
                          <input
                            type="radio"
                            class="btn-check"
                            name="radio-control-switch"
                            id="radio-control-switch-rigctld"
                            autocomplete="off"
                          />
                          <label
                            class="btn btn-sm btn-outline-secondary"
                            for="radio-control-switch-rigctld"
                          >
                            Hamlib
                          </label>
                        </div>
                        <div
                          class="btn-group btn-group-sm"
                          role="group"
                          aria-label="radio-control-switch-tci"
                        >
                          <input
                            type="radio"
                            class="btn-check"
                            name="radio-control-switch"
                            id="radio-control-switch-tci"
                            autocomplete="off"
                          />
                          <label
                            class="btn btn-sm btn-outline-secondary"
                            for="radio-control-switch-tci"
                          >
                            TCI
                          </label>
                        </div>
                      </div>
                    </div>

                    <div class="col-1 text-end">
                      <button
                        type="button"
                        id="openHelpModalRigControl"
                        data-bs-toggle="modal"
                        data-bs-target="#rigcontrolHelpModal"
                        class="btn m-0 p-0 border-0"
                      >
                        <i
                          class="bi bi-question-circle"
                          style="font-size: 1rem"
                        ></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="card-body p-2" style="height: 100px">
                <!-- RADIO CONTROL DISABLED -->
                <div id="radio-control-disabled">
                  <p class="small">
                    TNC will not utilize rig control and features will be
                    limited. While functional; it is recommended to configure
                    hamlib.
                  </p>
                </div>

                <!-- RADIO CONTROL RIGCTLD -->
                <div id="radio-control-rigctld">
                  <div class="input-group input-group-sm mb-1">
                    <div class="input-group input-group-sm mb-1">
                      <span class="input-group-text">Rigctld</span>
                      <span class="input-group-text">Address</span>
                      <input
                        type="text"
                        class="form-control"
                        placeholder="rigctld IP"
                        id="hamlib_rigctld_ip"
                        aria-label="Device IP"
                        aria-describedby="basic-addon1"
                      />
                      <span class="input-group-text">Port</span>
                      <input
                        type="text"
                        class="form-control"
                        placeholder="rigctld port"
                        id="hamlib_rigctld_port"
                        aria-label="Device Port"
                        aria-describedby="basic-addon1"
                      />
                    </div>

                    <div class="input-group input-group-sm mb-1">
                      <span class="input-group-text">Rigctld</span>
                      <button
                        class="btn btn-outline-success"
                        type="button"
                        id="hamlib_rigctld_start"
                      >
                        Start
                      </button>
                      <button
                        class="btn btn-outline-danger"
                        type="button"
                        id="hamlib_rigctld_stop"
                      >
                        Stop
                      </button>
                      <input
                        type="text"
                        class="form-control"
                        placeholder="Status"
                        id="hamlib_rigctld_status"
                        aria-label="State"
                        aria-describedby="basic-addon1"
                      />

                      <button
                        type="button"
                        id="testHamlib"
                        class="btn btn-sm btn-outline-secondary ms-1"
                        data-bs-placement="bottom"
                        data-bs-toggle="tooltip"
                        data-bs-trigger="hover"
                        data-bs-html="true"
                        title="Test your hamlib settings and toggle PTT once. Button will become <strong class='text-success'>green</strong> on success and <strong class='text-danger'>red</strong> if fails."
                      >
                        PTT Test
                      </button>
                    </div>
                  </div>
                </div>
                <!-- RADIO CONTROL TCI-->
                <div id="radio-control-tci">
                  <div class="input-group input-group-sm mb-1">
                    <div class="input-group input-group-sm mb-1">
                      <span class="input-group-text">TCI</span>
                      <span class="input-group-text">Address</span>
                      <input
                        type="text"
                        class="form-control"
                        placeholder="tci IP"
                        id="tci_ip"
                        aria-label="Device IP"
                        aria-describedby="basic-addon1"
                      />
                    </div>

                    <div class="input-group input-group-sm mb-1">
                      <span class="input-group-text">Port</span>
                      <input
                        type="text"
                        class="form-control"
                        placeholder="tci port"
                        id="tci_port"
                        aria-label="Device Port"
                        aria-describedby="basic-addon1"
                      />
                    </div>
                  </div>
                </div>
                <!-- RADIO CONTROL HELP -->
                <div id="radio-control-help">
                  <strong>VOX:</strong> Use rig control mode 'none'
                  <br />
                  <strong>HAMLIB locally:</strong> configure in settings, then
                  start/stop service.
                  <br />
                  <strong>HAMLIB remotely:</strong> Enter IP/Port, connection
                  happens automatically.
                </div>
              </div>
              <!--<div class="card-footer text-muted small" id="hamlib_info_field">
                Define TNC rig control mode (none/hamlib)
              </div>
              -->
            </div>
          </template>