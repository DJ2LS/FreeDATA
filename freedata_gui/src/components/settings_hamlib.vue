<script setup>
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { useSerialStore } from "../store/serialStore.js";

// Pinia setup
import { setActivePinia } from "pinia";
import pinia from "../store/index";
setActivePinia(pinia);

const serialStore = useSerialStore(pinia);

/*
const settings = ref({
  remote: {
    RIGCTLD: {
      ip: '',
      port: 0,
      enable_vfo: false
    },
    RADIO: {
      control: '',
      model_id: 0
    }
  }
});
*/

</script>

<template>
  <!-- Rigctld IP -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.hamlibrictldhost') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.hamlibrictldhost_help')"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <input
      type="text"
      class="form-control"
      :placeholder="$t('settings.radio.hamlibrictldhost_placeholder')"
      id="rigctldIp"
      aria-label="Rigctld IP"
      @change="onChange"
      v-model="settings.remote.RIGCTLD.ip"
    />
  </div>

  <!-- Rigctld Port -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.hamlibrigctldport') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.hamlibrigctldport_help')"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <input
      type="number"
      class="form-control"
      :placeholder="$t('settings.radio.hamlibrigctldport_placeholder')"
      id="rigctldPort"
      aria-label="Rigctld Port"
      @change="onChange"
      v-model.number="settings.remote.RIGCTLD.port"
    />
  </div>

  <!-- Rigctld VFO Parameter -->
  <div class="input-group input-group-sm mb-1">
    <label class="input-group-text w-50 text-wrap">
      {{ $t('settings.radio.hamlibrigctldenablevfo') }}
      <button
        type="button"
        class="btn btn-link p-0 ms-2"
        data-bs-toggle="tooltip"
        :title="$t('settings.radio.hamlibrigctldenablevfo_help')"
      >
        <i class="bi bi-question-circle"></i>
      </button>
    </label>
    <label class="input-group-text w-50">
      <div class="form-check form-switch form-check-inline">
        <input
          class="form-check-input"
          type="checkbox"
          id="enableVfoSwitch"
          v-model="settings.remote.RIGCTLD.enable_vfo"
          @change="onChange"
        />
        <label class="form-check-label" for="enableVfoSwitch">{{ $t('settings.enable') }}</label>
      </div>
    </label>
  </div>

  <hr class="m-2" />

  <!-- Conditional Section for Rigctld Bundle -->
  <div :class="settings.remote.RADIO.control == 'rigctld_bundle' ? '' : 'd-none'">
    <!-- Radio Model -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctldradiomodel') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctldradiomodel_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        aria-label="Radio Model"
        id="radioModelSelect"
        @change="onChange"
        v-model.number="settings.remote.RADIO.model_id"
      >
        <!-- Your extensive list of options -->
<option selected value="0">-- ignore --</option>
        <option value="1">Hamlib Dummy</option>
        <option value="2">Hamlib NET rigctl</option>
        <option value="4">FLRig FLRig</option>
        <option value="5">TRXManager TRXManager 5.7.630+</option>
        <option value="6">Hamlib Dummy No VFO</option>
        <option value="29001">ADAT www.adat.ch (29001)</option>
        <option value="25016">AE9RB Si570 (25016)</option>
        <option value="25017">AE9RB Si570 (25017)</option>
        <option value="17001">Alinco DX-77 (17001)</option>
        <option value="17002">Alinco DX-SR8 (17002)</option>
        <option value="25006">AmQRP DDS-60 (25006)</option>
        <option value="25013">AMSAT-UK FUNcube (25013)</option>
        <option value="25018">AMSAT-UK FUNcube (25018)</option>
        <option value="5008">AOR AR2700 (5008)</option>
        <option value="5006">AOR AR3000A (5006)</option>
        <option value="5005">AOR AR3030 (5005)</option>
        <option value="5004">AOR AR5000 (5004)</option>
        <option value="5014">AOR AR5000A (5014)</option>
        <option value="5003">AOR AR7030 (5003)</option>
        <option value="5015">AOR AR7030 (5015)</option>
        <option value="5002">AOR AR8000 (5002)</option>
        <option value="5001">AOR AR8200 (5001)</option>
        <option value="5013">AOR AR8600 (5013)</option>
        <option value="5016">AOR SR2200 (5016)</option>
        <option value="32001">Barrett 2050 (32001)</option>
        <option value="32003">Barrett 4050 (32003)</option>
        <option value="32002">Barrett 950 (32002)</option>
        <option value="34001">CODAN Envoy (34001)</option>
        <option value="34002">CODAN NGT (34002)</option>
        <option value="25003">Coding Technologies (25003)</option>
        <option value="31002">Dorji DRA818U (31002)</option>
        <option value="31001">Dorji DRA818V (31001)</option>
        <option value="9002">Drake R-8A (9002)</option>
        <option value="9003">Drake R-8B (9003)</option>
        <option value="23003">DTTS Microwave (23003)</option>
        <option value="23004">DTTS Microwave (23004)</option>
        <option value="33001">ELAD FDM-DUO (33001)</option>
        <option value="2021">Elecraft K2 (2021)</option>
        <option value="2029">Elecraft K3 (2029)</option>
        <option value="2043">Elecraft K3S (2043)</option>
        <option value="2047">Elecraft K4 (2047)</option>
        <option value="2044">Elecraft KX2 (2044)</option>
        <option value="2045">Elecraft KX3 (2045)</option>
        <option value="2038">Elecraft XG3 (2038)</option>
        <option value="25001">Elektor Elektor (25001)</option>
        <option value="25007">Elektor Elektor (25007)</option>
        <option value="25012">FiFi FiFi-SDR (25012)</option>
        <option value="2036">FlexRadio 6xxx (2036)</option>
        <option value="23001">Flex-radio SDR-1000 (23001)</option>
        <option value="2048">FlexRadio/ANAN PowerSDR/Thetis (2048)</option>
        <option value="25015">Funkamateur FA-SDR (25015)</option>
        <option value="35001">GOMSPACE GS100 (35001)</option>
        <option value="2046">Hilberling PT-8000A (2046)</option>
        <option value="25019">HobbyPCB RS-HFIQ (25019)</option>
        <option value="3054">Icom IC (3054)</option>
        <option value="3002">Icom IC-1275 (3002)</option>
        <option value="3003">Icom IC-271 (3003)</option>
        <option value="3072">Icom IC-2730 (3072)</option>
        <option value="3004">Icom IC-275 (3004)</option>
        <option value="3005">Icom IC-375 (3005)</option>
        <option value="3006">Icom IC-471 (3006)</option>
        <option value="3007">Icom IC-475 (3007)</option>
        <option value="3008">Icom IC-575 (3008)</option>
        <option value="3060">Icom IC-7000 (3060)</option>
        <option value="3055">Icom IC-703 (3055)</option>
        <option value="3085">Icom IC-705 (3085)</option>
        <option value="3009">Icom IC-706 (3009)</option>
        <option value="3010">Icom IC-706MkII (3010)</option>
        <option value="3011">Icom IC-706MkIIG (3011)</option>
        <option value="3012">Icom IC-707 (3012)</option>
        <option value="3070">Icom IC-7100 (3070)</option>
        <option value="3013">Icom IC-718 (3013)</option>
        <option value="3061">Icom IC-7200 (3061)</option>
        <option value="3014">Icom IC-725 (3014)</option>
        <option value="3015">Icom IC-726 (3015)</option>
        <option value="3016">Icom IC-728 (3016)</option>
        <option value="3017">Icom IC-729 (3017)</option>
        <option value="3073">Icom IC-7300 (3073)</option>
        <option value="3019">Icom IC-735 (3019)</option>
        <option value="3020">Icom IC-736 (3020)</option>
        <option value="3021">Icom IC-737 (3021)</option>
        <option value="3022">Icom IC-738 (3022)</option>
        <option value="3067">Icom IC-7410 (3067)</option>
        <option value="3023">Icom IC-746 (3023)</option>
        <option value="3046">Icom IC-746PRO (3046)</option>
        <option value="3024">Icom IC-751 (3024)</option>
        <option value="3026">Icom IC-756 (3026)</option>
        <option value="3027">Icom IC-756PRO (3027)</option>
        <option value="3047">Icom IC-756PROII (3047)</option>
        <option value="3057">Icom IC-756PROIII (3057)</option>
        <option value="3063">Icom IC-7600 (3063)</option>
        <option value="3028">Icom IC-761 (3028)</option>
        <option value="3078">Icom IC-7610 (3078)</option>
        <option value="3029">Icom IC-765 (3029)</option>
        <option value="3062">Icom IC-7700 (3062)</option>
        <option value="3030">Icom IC-775 (3030)</option>
        <option value="3045">Icom IC-78 (3045)</option>
        <option value="3056">Icom IC-7800 (3056)</option>
        <option value="3031">Icom IC-781 (3031)</option>
        <option value="3075">Icom IC-7850/7851 (3075)</option>
        <option value="3032">Icom IC-820H (3032)</option>
        <option value="3034">Icom IC-821H (3034)</option>
        <option value="3044">Icom IC-910 (3044)</option>
        <option value="3068">Icom IC-9100 (3068)</option>
        <option value="3065">Icom IC-92D (3065)</option>
        <option value="3035">Icom IC-970 (3035)</option>
        <option value="3081">Icom IC-9700 (3081)</option>
        <option value="3086">Icom IC-F8101 (3086)</option>
        <option value="30001">Icom IC-M700PRO (30001)</option>
        <option value="30003">Icom IC-M710 (30003)</option>
        <option value="30002">Icom IC-M802 (30002)</option>
        <option value="30004">Icom IC-M803 (30004)</option>
        <option value="4002">Icom IC-PCR100 (4002)</option>
        <option value="4001">Icom IC-PCR1000 (4001)</option>
        <option value="4003">Icom IC-PCR1500 (4003)</option>
        <option value="4004">Icom IC-PCR2500 (4004)</option>
        <option value="3036">Icom IC-R10 (3036)</option>
        <option value="3058">Icom IC-R20 (3058)</option>
        <option value="3080">Icom IC-R30 (3080)</option>
        <option value="3077">Icom IC-R6 (3077)</option>
        <option value="3040">Icom IC-R7000 (3040)</option>
        <option value="3037">Icom IC-R71 (3037)</option>
        <option value="3041">Icom IC-R7100 (3041)</option>
        <option value="3038">Icom IC-R72 (3038)</option>
        <option value="3039">Icom IC-R75 (3039)</option>
        <option value="3042">Icom ICR-8500 (3042)</option>
        <option value="3079">Icom IC-R8600 (3079)</option>
        <option value="3043">Icom IC-R9000 (3043)</option>
        <option value="3066">Icom IC-R9500 (3066)</option>
        <option value="3069">Icom IC-RX7 (3069)</option>
        <option value="3083">Icom ID-31 (3083)</option>
        <option value="3082">Icom ID-4100 (3082)</option>
        <option value="3084">Icom ID-51 (3084)</option>
        <option value="3071">Icom ID-5100 (3071)</option>
        <option value="6001">JRC JST-145 (6001)</option>
        <option value="6002">JRC JST-245 (6002)</option>
        <option value="6005">JRC NRD-525 (6005)</option>
        <option value="6006">JRC NRD-535D (6006)</option>
        <option value="6007">JRC NRD-545 (6007)</option>
        <option value="18001">Kachina 505DSP (18001)</option>
        <option value="2015">Kenwood R-5000 (2015)</option>
        <option value="2033">Kenwood TH-D72A (2033)</option>
        <option value="2042">Kenwood TH-D74 (2042)</option>
        <option value="2017">Kenwood TH-D7A (2017)</option>
        <option value="2019">Kenwood TH-F6A (2019)</option>
        <option value="2020">Kenwood TH-F7E (2020)</option>
        <option value="2023">Kenwood TH-G71 (2023)</option>
        <option value="2026">Kenwood TM-D700 (2026)</option>
        <option value="2034">Kenwood TM-D710(G) (2034)</option>
        <option value="2027">Kenwood TM-V7 (2027)</option>
        <option value="2035">Kenwood TM-V71(A) (2035)</option>
        <option value="2030">Kenwood TRC-80 (2030)</option>
        <option value="2025">Kenwood TS-140S (2025)</option>
        <option value="2014">Kenwood TS-2000 (2014)</option>
        <option value="2002">Kenwood TS-440S (2002)</option>
        <option value="2003">Kenwood TS-450S (2003)</option>
        <option value="2028">Kenwood TS-480 (2028)</option>
        <option value="2001">Kenwood TS-50S (2001)</option>
        <option value="2004">Kenwood TS-570D (2004)</option>
        <option value="2016">Kenwood TS-570S (2016)</option>
        <option value="2031">Kenwood TS-590S (2031)</option>
        <option value="2037">Kenwood TS-590SG (2037)</option>
        <option value="2024">Kenwood TS-680S (2024)</option>
        <option value="2005">Kenwood TS-690S (2005)</option>
        <option value="2006">Kenwood TS-711 (2006)</option>
        <option value="2007">Kenwood TS-790 (2007)</option>
        <option value="2008">Kenwood TS-811 (2008)</option>
        <option value="2009">Kenwood TS-850 (2009)</option>
        <option value="2010">Kenwood TS-870S (2010)</option>
        <option value="2041">Kenwood TS-890S (2041)</option>
        <option value="2022">Kenwood TS-930 (2022)</option>
        <option value="2011">Kenwood TS-940S (2011)</option>
        <option value="2012">Kenwood TS-950S (2012)</option>
        <option value="2013">Kenwood TS-950SDX (2013)</option>
        <option value="2039">Kenwood TS-990S (2039)</option>
        <option value="25011">KTH-SDR kit (25011)</option>
        <option value="2050">Lab599 TX-500 (2050)</option>
        <option value="10004">Lowe HF-235 (10004)</option>
        <option value="1045">M0NKA mcHF (1045)</option>
        <option value="2049">Malachite DSP (2049)</option>
        <option value="3074">Microtelecom Perseus (3074)</option>
        <option value="25008">mRS miniVNA (25008)</option>
        <option value="25014">N2ADR HiQSDR (25014)</option>
        <option value="2040">OpenHPSDR PiHPSDR (2040)</option>
        <option value="3053">Optoelectronics OptoScan456 (3053)</option>
        <option value="3052">Optoelectronics OptoScan535 (3052)</option>
        <option value="28001">Philips/Simoco PRM8060 (28001)</option>
        <option value="11005">Racal RA3702 (11005)</option>
        <option value="11003">Racal RA6790/GM (11003)</option>
        <option value="8004">Radio Shack (8004)</option>
        <option value="24001">RFT EKD-500 (24001)</option>
        <option value="27002">Rohde&Schwarz EB200 (27002)</option>
        <option value="27004">Rohde&Schwarz EK895/6 (27004)</option>
        <option value="27001">Rohde&Schwarz ESMC (27001)</option>
        <option value="27003">Rohde&Schwarz XK2100 (27003)</option>
        <option value="25002">SAT-Schneider DRT1 (25002)</option>
        <option value="2051">SDRPlay SDRUno (2051)</option>
        <option value="2032">SigFox Transfox (2032)</option>
        <option value="14004">Skanti TRP (14004)</option>
        <option value="14002">Skanti TRP8000 (14002)</option>
        <option value="25009">SoftRock Si570 (25009)</option>
        <option value="22001">TAPR DSP-10 (22001)</option>
        <option value="3064">Ten-Tec Delta (3064)</option>
        <option value="3051">Ten-Tec Omni (3051)</option>
        <option value="16003">Ten-Tec RX-320 (16003)</option>
        <option value="16012">Ten-Tec RX-331 (16012)</option>
        <option value="16004">Ten-Tec RX-340 (16004)</option>
        <option value="16005">Ten-Tec RX-350 (16005)</option>
        <option value="16007">Ten-Tec TT-516 (16007)</option>
        <option value="16002">Ten-Tec TT-538 (16002)</option>
        <option value="16001">Ten-Tec TT-550 (16001)</option>
        <option value="16008">Ten-Tec TT-565 (16008)</option>
        <option value="16009">Ten-Tec TT-585 (16009)</option>
        <option value="16011">Ten-Tec TT-588 (16011)</option>
        <option value="16013">Ten-Tec TT-599 (16013)</option>
        <option value="8002">Uniden BC245xlt (8002)</option>
        <option value="8006">Uniden BC250D (8006)</option>
        <option value="8001">Uniden BC780xlt (8001)</option>
        <option value="8003">Uniden BC895xlt (8003)</option>
        <option value="8012">Uniden BC898T (8012)</option>
        <option value="8010">Uniden BCD-396T (8010)</option>
        <option value="8011">Uniden BCD-996T (8011)</option>
        <option value="1033">Vertex Standard (1033)</option>
        <option value="26001">Video4Linux SW/FM (26001)</option>
        <option value="26002">Video4Linux2 SW/FM (26002)</option>
        <option value="12004">Watkins-Johnson WJ-8888 (12004)</option>
        <option value="15001">Winradio WR-1000 (15001)</option>
        <option value="15002">Winradio WR-1500 (15002)</option>
        <option value="15003">Winradio WR-1550 (15003)</option>
        <option value="15004">Winradio WR-3100 (15004)</option>
        <option value="15005">Winradio WR-3150 (15005)</option>
        <option value="15006">Winradio WR-3500 (15006)</option>
        <option value="15007">Winradio WR-3700 (15007)</option>
        <option value="15009">Winradio WR-G313 (15009)</option>
        <option value="3088">Xiegu G90 (3088)</option>
        <option value="3076">Xiegu X108G (3076)</option>
        <option value="3089">Xiegu X5105 (3089)</option>
        <option value="3087">Xiegu X6100 (3087)</option>
        <option value="1017">Yaesu FRG-100 (1017)</option>
        <option value="1019">Yaesu FRG-8800 (1019)</option>
        <option value="1018">Yaesu FRG-9600 (1018)</option>
        <option value="1021">Yaesu FT-100 (1021)</option>
        <option value="1003">Yaesu FT-1000D (1003)</option>
        <option value="1024">Yaesu FT-1000MP (1024)</option>
        <option value="1029">Yaesu FT-2000 (1029)</option>
        <option value="1027">Yaesu FT-450 (1027)</option>
        <option value="1046">Yaesu FT-450D (1046)</option>
        <option value="1039">Yaesu FT-600 (1039)</option>
        <option value="1047">Yaesu FT-650 (1047)</option>
        <option value="1049">Yaesu FT-710 (1049)</option>
        <option value="1010">Yaesu FT-736R (1010)</option>
        <option value="1005">Yaesu FT-747GX (1005)</option>
        <option value="1006">Yaesu FT-757GX (1006)</option>
        <option value="1007">Yaesu FT-757GXII (1007)</option>
        <option value="1009">Yaesu FT-767GX (1009)</option>
        <option value="1020">Yaesu FT-817 (1020)</option>
        <option value="1041">Yaesu FT-818 (1041)</option>
        <option value="1011">Yaesu FT-840 (1011)</option>
        <option value="1001">Yaesu FT-847 (1001)</option>
        <option value="1038">Yaesu FT-847UNI (1038)</option>
        <option value="1022">Yaesu FT-857 (1022)</option>
        <option value="1015">Yaesu FT-890 (1015)</option>
        <option value="1036">Yaesu FT-891 (1036)</option>
        <option value="1023">Yaesu FT-897 (1023)</option>
        <option value="1043">Yaesu FT-897D (1043)</option>
        <option value="1013">Yaesu FT-900 (1013)</option>
        <option value="1014">Yaesu FT-920 (1014)</option>
        <option value="1028">Yaesu FT-950 (1028)</option>
        <option value="1031">Yaesu FT-980 (1031)</option>
        <option value="1016">Yaesu FT-990 (1016)</option>
        <option value="1048">Yaesu FT-990 (1048)</option>
        <option value="1035">Yaesu FT-991 (1035)</option>
        <option value="1042">Yaesu FTDX-10 (1042)</option>
        <option value="1040">Yaesu FTDX-101D (1040)</option>
        <option value="1044">Yaesu FTDX-101MP (1044)</option>
        <option value="1034">Yaesu FTDX-1200 (1034)</option>
        <option value="1037">Yaesu FTDX-3000 (1037)</option>
        <option value="1032">Yaesu FTDX-5000 (1032)</option>
        <option value="1030">Yaesu FTDX-9000 (1030)</option>
        <option value="1004">Yaesu MARK-V (1004)</option>
        <option value="1025">Yaesu MARK-V (1025)</option>
        <option value="1026">Yaesu VR-5000 (1026)</option>
      </select>
    </div>

    <!-- Radio Port -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctldcomport') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctldcomport_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        @change="onChange"
        v-model="settings.remote.RADIO.serial_port"
      >
        <option
          v-for="device in serialStore.serialDevices"
          :value="device.port"
          :key="device.port"
        >
          {{ device.description }}
        </option>
      </select>
    </div>

        <!-- Radio Custom Port -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctldcustomcomport') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctldcustomcomport_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>

      <input
        type="text"
        class="form-control"
        placeholder="settings.remote.RADIO.serial_port.port"
        id="rigctldIp"
        aria-label="Rigctld IP"
        @change="onChange"
        v-model="settings.remote.RADIO.serial_port"
      />
    </div>

    <!-- Serial Speed -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctldserialspeed') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctldserialspeed_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        id="serialSpeedSelect"
        @change="onChange"
        v-model.number="settings.remote.RADIO.serial_speed"
      >
        <option selected value="0">-- ignore --</option>
        <option value="1200">1200</option>
        <option value="2400">2400</option>
        <option value="4800">4800</option>
        <option value="9600">9600</option>
        <option value="19200">19200</option>
        <option value="38400">38400</option>
        <option value="57600">57600</option>
        <option value="115200">115200</option>
      </select>
    </div>

    <!-- Data Bits -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctlddatabits') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctlddatabits_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        id="dataBitsSelect"
        @change="onChange"
        v-model.number="settings.remote.RADIO.data_bits"
      >
        <option selected value="0">-- ignore --</option>
        <option value="7">7</option>
        <option value="8">8</option>
      </select>
    </div>

    <!-- Stop Bits -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctldstopbits') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctldstopbits_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        id="stopBitsSelect"
        @change="onChange"
        v-model.number="settings.remote.RADIO.stop_bits"
      >
        <option selected value="0">-- ignore --</option>
        <option value="1">1</option>
        <option value="2">2</option>
      </select>
    </div>

    <!-- Serial Handshake -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctldhandshake') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctldhandshake_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        id="serialHandshakeSelect"
        @change="onChange"
        v-model="settings.remote.RADIO.serial_handshake"
      >
        <option selected value="ignore">-- ignore --</option>
        <option value="None">None (Default)</option>
        <!-- Add more options if needed -->
      </select>
    </div>

    <!-- PTT Device Port -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctldpttdeviceport') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctldpttdeviceport_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        @change="onChange"
        v-model="settings.remote.RADIO.ptt_port"
      >
        <option
          v-for="device in serialStore.serialDevices"
          :value="device.port"
          :key="device.port"
        >
          {{ device.description }}
        </option>
      </select>
    </div>

    <!-- PTT Type -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctldptttype') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctldptttype_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        id="pttTypeSelect"
        @change="onChange"
        v-model="settings.remote.RADIO.ptt_type"
      >
        <option selected value="ignore">-- ignore --</option>
        <option value="NONE">NONE</option>
        <option value="RIG">RIG</option>
        <option value="USB">USB</option>
        <option value="RTS">Serial RTS</option>
        <option value="PARALLEL">Rig PARALLEL</option>
        <option value="MICDATA">Rig MICDATA</option>
        <option value="CM108">Rig CM108</option>
      </select>
    </div>

    <!-- DCD -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctlddcd') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctlddcd_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        id="dcdSelect"
        @change="onChange"
        v-model="settings.remote.RADIO.serial_dcd"
      >
        <option selected value="ignore">-- ignore --</option>
        <option value="NONE">NONE</option>
        <option value="RIG">RIG/CAT</option>
        <option value="DSR">DSR</option>
        <option value="CTS">CTS</option>
        <option value="CD">CD</option>
        <option value="PARALLEL">PARALLEL</option>
      </select>
    </div>

    <!-- DTR -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctlddtr') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctlddtr_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <select
        class="form-select form-select-sm w-50"
        id="dtrSelect"
        @change="onChange"
        v-model="settings.remote.RADIO.serial_dtr"
      >
        <option selected value="ignore">-- ignore --</option>
        <option value="OFF">OFF</option>
        <option value="ON">ON</option>
      </select>
    </div>

    <!-- Rigctld Command -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctldcommand') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctldcommand_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <input
        type="text"
        class="form-control"
        id="rigctldCommand"
        aria-label="Rigctld Command"
        disabled
        :placeholder="$t('settings.radio.hamlibrigctldcommand_placeholder')"
      />
      <button
        class="btn btn-outline-secondary"
        type="button"
        id="btnHamlibCopyCommand"
      >
        <i id="btnHamlibCopyCommandBi" class="bi bi-clipboard"></i>
      </button>
    </div>

    <!-- Rigctld Custom Arguments -->
    <div class="input-group input-group-sm mb-1">
      <label class="input-group-text w-50 text-wrap">
        {{ $t('settings.radio.hamlibrigctldcustomarguments') }}
        <button
          type="button"
          class="btn btn-link p-0 ms-2"
          data-bs-toggle="tooltip"
          :title="$t('settings.radio.hamlibrigctldcustomarguments_help')"
        >
          <i class="bi bi-question-circle"></i>
        </button>
      </label>
      <input
        type="text"
        class="form-control"
        :placeholder="$t('settings.radio.hamlibrigctldcustomarguments_placeholder')"
        id="rigctldCustomArgs"
        aria-label="Rigctld Custom Arguments"
        @change="onChange"
        v-model="settings.remote.RIGCTLD.arguments"
      />
    </div>
  </div>
</template>
