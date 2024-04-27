<template>

            <div class="container">
              <nav>
                <div class="nav nav-tabs" id="nav-tab-mesh" role="tablist-mesh">
                  <button
                    class="nav-link active"
                    id="nav-route-tab"
                    data-bs-toggle="tab"
                    data-bs-target="#nav-route"
                    type="button"
                    role="tab"
                    aria-controls="nav-route"
                    aria-selected="true"
                  >
                    Routes
                  </button>
                  <button
                    class="nav-link"
                    id="nav-signaling-tab"
                    data-bs-toggle="tab"
                    data-bs-target="#nav-signaling"
                    type="button"
                    role="tab"
                    aria-controls="nav-signaling"
                    aria-selected="false"
                  >
                    Signaling
                  </button>
                  <button
                    class="nav-link"
                    id="nav-actions-tab"
                    data-bs-toggle="tab"
                    data-bs-target="#nav-actions"
                    type="button"
                    role="tab"
                    aria-controls="nav-actions"
                    aria-selected="false"
                  >
                    Actions
                  </button>
                </div>
              </nav>

              <div class="tab-content d-none" id="nav-tabContent-Mesh">
                <div
                  class="tab-pane fade show active vw-100 vh-90 overflow-auto"
                  id="nav-route"
                  role="tabpanel"
                  aria-labelledby="nav-route-tab"
                >
                  <div class="container-fluid">
                    <div
                      class="table-responsive overflow-auto"
                      style="max-width: 99vw; max-height: 99vh"
                    >
                      <table class="table table-hover table-sm">
                        <thead>
                          <tr>
                            <th scope="col">Timestamp</th>
                            <th scope="col">DXCall</th>
                            <th scope="col">Router</th>
                            <th scope="col">Hops</th>
                            <th scope="col">Score</th>
                            <th scope="col">SNR</th>
                          </tr>
                        </thead>
                        <tbody id="mesh-table"></tbody>
                      </table>
                    </div>
                  </div>
                </div>
                <div
                  class="tab-pane fade"
                  id="nav-signaling"
                  role="tabpanel"
                  aria-labelledby="nav-signaling-tab"
                >
                  <div class="container-fluid">
                    <div
                      class="table-responsive overflow-auto"
                      style="max-width: 99vw; max-height: 99vh"
                    >
                      <table class="table table-hover table-sm">
                        <thead>
                          <tr>
                            <th scope="col">Timestamp</th>
                            <th scope="col">Destination</th>
                            <th scope="col">Origin</th>
                            <th scope="col">Frametype</th>
                            <th scope="col">Payload</th>
                            <th scope="col">Attempt</th>
                            <th scope="col">Status</th>
                          </tr>
                        </thead>
                        <tbody id="mesh-signalling-table"></tbody>
                      </table>
                    </div>
                  </div>
                </div>

                <div
                  class="tab-pane fade"
                  id="nav-actions"
                  role="tabpanel-mesh"
                  aria-labelledby="nav-actions-tab"
                >
                  <div class="input-group mt-1">
                    <input
                      type="text"
                      class="form-control"
                      style="max-width: 6rem; text-transform: uppercase"
                      placeholder="DXcall"
                      pattern="[A-Z]*"
                      id="dxCallMesh"
                      maxlength="11"
                      aria-label="Input group"
                      aria-describedby="btnGroupAddon"
                    />
                    <button
                      id="transmit_mesh_ping"
                      type="button"
                      class="btn btn-primary"
                    >
                      mesh ping
                    </button>
                  </div>
                </div>
              </div>
            </div>
</template>