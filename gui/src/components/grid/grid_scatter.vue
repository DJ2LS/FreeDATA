<script setup lang="ts">
// @ts-nocheck
// reason for no check is, that we have some mixing of typescript and chart js which seems to be not to be fixed that easy
import { computed, onMounted } from "vue";
import { setActivePinia } from "pinia";
import pinia from "../../store/index";
setActivePinia(pinia);

import { useStateStore } from "../../store/stateStore.js";
const state = useStateStore(pinia);

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Scatter } from "vue-chartjs";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

// https://www.chartjs.org/docs/latest/samples/line/segments.html
const scatterChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    x: {
      type: "linear",
      position: "bottom",
      grid: {
        display: true,
        lineWidth: 1, // Set the line width for x-axis grid lines
      },
      ticks: {
        display: true,
      },
    },
    y: {
      type: "linear",
      position: "left",
      grid: {
        display: true,
        lineWidth: 1, // Set the line width for y-axis grid lines
      },
      ticks: {
        display: true,
      },
    },
  },
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      enabled: false,
    },
  },
};

const scatterChartData = computed(() => ({
  datasets: [
    {
      type: "scatter",
      fill: true,
      data: state.scatter,
      label: "Scatter",
      tension: 0.1,
      borderColor: "rgb(0, 255, 0)",
    },
  ],
}));
</script>

<template>
  <div class="w-100 h-100">
    <Scatter :data="scatterChartData" :options="scatterChartOptions" />
  </div>
  <!--278px-->
</template>
