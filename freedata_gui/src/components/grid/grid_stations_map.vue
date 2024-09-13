<template>
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <div class="btn-group btn-group-sm" role="group">
        <button @click="zoomIn" class="btn btn-sm btn-outline-secondary"><i class="bi bi-plus-square"></i></button>
        <button @click="centerMap" class="btn btn-sm btn-secondary"><i class="bi bi-house-door"></i></button>
        <button @click="zoomOut" class="btn btn-sm btn-outline-secondary"><i class="bi bi-dash-square"></i></button>
      </div>

      <div class="input-group input-group-sm ms-2">
        <input type="text" class="form-control w-100" placeholder="Station" aria-label="Username" aria-describedby="basic-addon1" v-model="infoText" disabled>
      </div>
    </div>
    <div class="card-body">
      <div ref="mapContainer" class="map-container"></div>
      <div :style="popupStyle" class="popup">{{ infoText }}</div>
    </div>
  </div>
</template>

<script setup>
import { settingsStore as settings } from '../../store/settingsStore.js';
import { ref, onMounted, onBeforeUnmount, nextTick, watch, toRaw } from 'vue';
import * as d3 from 'd3';
import { feature } from 'topojson-client';
import { locatorToLatLng, distance } from 'qth-locator';
import { setActivePinia } from 'pinia';
import pinia from '../../store/index'; // Import your Pinia instance
import { useStateStore } from '../../store/stateStore.js';

// Activate Pinia
setActivePinia(pinia);
const state = useStateStore(pinia);

const mapContainer = ref(null);
const infoText = ref('');
const popupStyle = ref({});
let svg, path, projection, zoom;
const basePinRadius = 5; // Base radius for pins
let actualPinRadius = basePinRadius;

// Function to get distance between two grid squares
function getMaidenheadDistance(dxGrid) {
  try {
    return parseInt(distance(settings.remote.STATION.mygrid, dxGrid));
  } catch (e) {
    console.error('Error calculating distance:', e);
    return null;
  }
}

// Function to draw the map
const drawMap = () => {
  const containerWidth = mapContainer.value.clientWidth;
  const containerHeight = mapContainer.value.clientHeight;

  // Clear existing SVG if it exists
  if (svg) {
    svg.remove();
  }

  // Create Mercator projection
  projection = d3.geoMercator()
    .scale(containerWidth / (2 * Math.PI))
    .translate([containerWidth / 2, containerHeight / 2]);

  path = d3.geoPath().projection(projection);

  // Create SVG element
  svg = d3.select(mapContainer.value)
    .append('svg')
    .attr('width', '100%')
    .attr('height', '100%')
    .attr('viewBox', `0 0 ${containerWidth} ${containerHeight}`)
    .attr('preserveAspectRatio', 'xMidYMid meet');

  // Set up zoom behavior
  zoom = d3.zoom()
    .scaleExtent([1, 8])
    .on('zoom', (event) => {
      svg.selectAll('g').attr('transform', event.transform);

      // Adjust pin size and line width with zoom
      actualPinRadius = basePinRadius / event.transform.k
      svg.selectAll('.pin').attr('r', actualPinRadius);
      svg.selectAll('.connection-line').attr('stroke-width', 1 / event.transform.k);
    });

  svg.call(zoom);

  // Import JSON data dynamically
  import('@/assets/countries-50m.json').then(worldData => {
    const countriesGeoJSON = feature(worldData, worldData.objects.countries);

    // Draw country paths
    const g = svg.append('g');

    g.selectAll('path')
      .data(countriesGeoJSON.features)
      .enter()
      .append('path')
      .attr('d', path)
      .attr('fill', '#ccc')
      .attr('stroke', '#333');

    // Draw initial pins and lines
    updatePinsAndLines(g);
  });
};

// Function to update pins and draw lines
const updatePinsAndLines = (g) => {
  // Remove existing pins and lines
  g.selectAll('.pin').remove();
  g.selectAll('.connection-line').remove();

  const heardStations = toRaw(state.heard_stations); // Ensure it's the raw data
  const points = [];

  // Prepare points for heard stations
heardStations.forEach(item => {
  // Ensure data is valid: 'gridsquare' must not be empty, '', or undefined, and 'origin' must be valid
  if (item.gridsquare && item.gridsquare.trim() !== '' && item.origin) {
    const [lat, lng] = locatorToLatLng(item.gridsquare); // Convert gridsquare to lat/lng
    points.push({ lat, lon: lng, origin: item.origin, gridsquare: item.gridsquare }); // Add to the points array
  }
});

  // Check if 'mygrid' is defined and not empty
  const mygrid = settings.remote.STATION.mygrid;
  if (mygrid) {
    // Your station's coordinates
    const [myLat, myLng] = locatorToLatLng(mygrid);
    const [myX, myY] = projection([myLng, myLat]); // Project your station's coordinates

    // Draw lines from your station to each heard station
    g.selectAll('.connection-line')
      .data(points)
      .enter()
      .append('line')
      .attr('class', 'connection-line')
      .attr('x1', myX)
      .attr('y1', myY)
      .attr('x2', d => projection([d.lon, d.lat])[0])
      .attr('y2', d => projection([d.lon, d.lat])[1])
      .attr('stroke', 'blue')
      .attr('stroke-width', 1)
      .attr('stroke-opacity', 0.5);
  } else {
    console.error('Error: Station grid square (mygrid) is not defined. Lines will not be drawn.');
  }

  // Add pins
  g.selectAll('.pin')
    .data(points)
    .enter()
    .append('circle')
    .attr('class', 'pin')
    .attr('r', actualPinRadius) // Set initial radius
    .attr('fill', 'red')
    .attr('cx', d => projection([d.lon, d.lat])[0])
    .attr('cy', d => projection([d.lon, d.lat])[1])
    .on('mouseover', (event, d) => {
      // Show info with station details
      infoText.value = `${d.origin} - ${d.gridsquare} (${getMaidenheadDistance(d.gridsquare)} km)`;
    })
    .on('mouseout', () => {
      infoText.value = '';
    });
};


// Handle window resize
const handleResize = () => {
  drawMap();
};

// Watch for changes in heard_stations and update pins accordingly
watch(state.heard_stations, (changedHeardStations) => {
  console.log('Heard stations updated:', toRaw(changedHeardStations));
  const g = svg.select('g');
  updatePinsAndLines(g);
});

// Zoom in function
const zoomIn = () => {
  svg.transition().call(zoom.scaleBy, 1.2);
};

// Zoom out function
const zoomOut = () => {
  svg.transition().call(zoom.scaleBy, 0.8);
};

// Center the map
const centerMap = () => {
  const mygrid = settings.remote.STATION.mygrid; // Get the grid square value
  if (!mygrid) {
    console.error('Error: Station grid square (mygrid) is not defined.');
    return; // Exit if 'mygrid' is not defined
  }

  const [lat, lng] = locatorToLatLng(mygrid); // Convert gridsquare to lat/lng

  // Project the geographic coordinates to SVG coordinates
  const [x, y] = projection([lng, lat]);

  // Center the map at the calculated coordinates
  svg.transition().duration(750).call(
    zoom.translateTo,
    x,
    y
  );
};

// Lifecycle hooks
onMounted(async () => {
  await nextTick();
  drawMap();
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 400px;
}

.pin {
  fill: red;
  stroke: black;
  stroke-width: 1px;
}

.path {
  fill: #ccc;
  stroke: #333;
}

.connection-line {
  stroke: blue;
  stroke-width: 1;
  stroke-opacity: 0.5;
}

.popup {
  background-color: white;
  border: 1px solid black;
  padding: 5px;
  position: absolute;
  display: none;
  z-index: 10; /* Ensure the popup is above other elements */
  pointer-events: none; /* Prevent mouse events on the popup */
}
</style>
