<script setup lang="ts">
import { settingsStore as settings, onChange } from "../store/settingsStore.js";
import { serialDeviceOptions } from "../js/deviceFormHelper";
</script>

<template>
  <hr class="m-2" />
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Rigctld IP</span>
    <input
      type="text"
      class="form-control"
      placeholder="rigctld IP"
      id="hamlib_rigctld_ip"
      aria-label="Device IP"
      @change="onChange"
      v-model="settings.remote.RIGCTLD.ip"
    />
  </div>

  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Rigctld port</span>
    <input
      type="text"
      class="form-control"
      placeholder="rigctld port"
      id="hamlib_rigctld_port"
      aria-label="Device Port"
      @change="onChange"
      v-model="settings.remote.RIGCTLD.port"
    />
  </div>

  <hr class="m-2" />
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Radio model</span>
    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="hamlib_deviceid"
      @change="onChange"
      v-model.number="settings.remote.RADIO.model_id"
    >
      <option selected value="-- ignore --">-- ignore --</option>
      <option value="2028">Kenwood TS480</option>
      <option value="1">Hamlib Dummy</option>
      <option value="2">Hamlib NET rigctl</option>
      <option value="4">FLRig FLRig</option>
      <option value="5">TRXManager TRXManager 5.7.630+</option>
      <option value="6">Hamlib Dummy No VFO</option>
      <option value="1001">Yaesu FT-847</option>
      <option value="1003">Yaesu FT-1000D</option>
      <option value="1004">Yaesu MARK-V FT-1000MP</option>
      <option value="1005">Yaesu FT-747GX</option>
      <option value="1006">Yaesu FT-757GX</option>
      <option value="1007">Yaesu FT-757GXII</option>
      <option value="1009">Yaesu FT-767GX</option>
      <option value="1010">Yaesu FT-736R</option>
      <option value="1011">Yaesu FT-840</option>
      <option value="1013">Yaesu FT-900</option>
      <option value="1014">Yaesu FT-920</option>
      <option value="1015">Yaesu FT-890</option>
      <option value="1016">Yaesu FT-990</option>
      <option value="1017">Yaesu FRG-100</option>
      <option value="1018">Yaesu FRG-9600</option>
      <option value="1019">Yaesu FRG-8800</option>
      <option value="1020">Yaesu FT-817</option>
      <option value="1021">Yaesu FT-100</option>
      <option value="1022">Yaesu FT-857</option>
      <option value="1023">Yaesu FT-897</option>
      <option value="1024">Yaesu FT-1000MP</option>
      <option value="1025">Yaesu MARK-V Field FT-1000MP</option>
      <option value="1026">Yaesu VR-5000</option>
      <option value="1027">Yaesu FT-450</option>
      <option value="1028">Yaesu FT-950</option>
      <option value="1029">Yaesu FT-2000</option>
      <option value="1030">Yaesu FTDX-9000</option>
      <option value="1031">Yaesu FT-980</option>
      <option value="1032">Yaesu FTDX-5000</option>
      <option value="1033">Vertex Standard VX-1700</option>
      <option value="1034">Yaesu FTDX-1200</option>
      <option value="1035">Yaesu FT-991</option>
      <option value="1036">Yaesu FT-891</option>
      <option value="1037">Yaesu FTDX-3000</option>
      <option value="1038">Yaesu FT-847UNI</option>
      <option value="1039">Yaesu FT-600</option>
      <option value="1040">Yaesu FTDX-101D</option>
      <option value="1041">Yaesu FT-818</option>
      <option value="1042">Yaesu FTDX-10</option>
      <option value="1043">Yaesu FT-897D</option>
      <option value="1044">Yaesu FTDX-101MP</option>
      <option value="2001">Kenwood TS-50S</option>
      <option value="2002">Kenwood TS-440S</option>
      <option value="2003">Kenwood TS-450S</option>
      <option value="2004">Kenwood TS-570D</option>
      <option value="2005">Kenwood TS-690S</option>
      <option value="2006">Kenwood TS-711</option>
      <option value="2007">Kenwood TS-790</option>
      <option value="2008">Kenwood TS-811</option>
      <option value="2009">Kenwood TS-850</option>
      <option value="2010">Kenwood TS-870S</option>
      <option value="2011">Kenwood TS-940S</option>
      <option value="2012">Kenwood TS-950S</option>
      <option value="2013">Kenwood TS-950SDX</option>
      <option value="2014">Kenwood TS-2000</option>
      <option value="2015">Kenwood R-5000</option>
      <option value="2016">Kenwood TS-570S</option>
      <option value="2017">Kenwood TH-D7A</option>
      <option value="2019">Kenwood TH-F6A</option>
      <option value="2020">Kenwood TH-F7E</option>
      <option value="2021">Elecraft K2</option>
      <option value="2022">Kenwood TS-930</option>
      <option value="2023">Kenwood TH-G71</option>
      <option value="2024">Kenwood TS-680S</option>
      <option value="2025">Kenwood TS-140S</option>
      <option value="2026">Kenwood TM-D700</option>
      <option value="2027">Kenwood TM-V7</option>
      <option value="2028">Kenwood TS-480</option>
      <option value="2029">Elecraft K3</option>
      <option value="2030">Kenwood TRC-80</option>
      <option value="2031">Kenwood TS-590S</option>
      <option value="2032">SigFox Transfox</option>
      <option value="2033">Kenwood TH-D72A</option>
      <option value="2034">Kenwood TM-D710(G)</option>
      <option value="2036">FlexRadio 6xxx</option>
      <option value="2037">Kenwood TS-590SG</option>
      <option value="2038">Elecraft XG3</option>
      <option value="2039">Kenwood TS-990s</option>
      <option value="2040">OpenHPSDR PiHPSDR</option>
      <option value="2041">Kenwood TS-890S</option>
      <option value="2042">Kenwood TH-D74</option>
      <option value="2043">Elecraft K3S</option>
      <option value="2044">Elecraft KX2</option>
      <option value="2045">Elecraft KX3</option>
      <option value="2046">Hilberling PT-8000A</option>
      <option value="2047">Elecraft K4</option>
      <option value="2048">FlexRadio/ANAN PowerSDR/Thetis</option>
      <option value="2049">Malachite DSP</option>
      <option value="3002">Icom IC-1275</option>
      <option value="3003">Icom IC-271</option>
      <option value="3004">Icom IC-275</option>
      <option value="3006">Icom IC-471</option>
      <option value="3007">Icom IC-475</option>
      <option value="3009">Icom IC-706</option>
      <option value="3010">Icom IC-706MkII</option>
      <option value="3011">Icom IC-706MkIIG</option>
      <option value="3012">Icom IC-707</option>
      <option value="3013">Icom IC-718</option>
      <option value="3014">Icom IC-725</option>
      <option value="3015">Icom IC-726</option>
      <option value="3016">Icom IC-728</option>
      <option value="3017">Icom IC-729</option>
      <option value="3019">Icom IC-735</option>
      <option value="3020">Icom IC-736</option>
      <option value="3021">Icom IC-737</option>
      <option value="3022">Icom IC-738</option>
      <option value="3023">Icom IC-746</option>
      <option value="3024">Icom IC-751</option>
      <option value="3026">Icom IC-756</option>
      <option value="3027">Icom IC-756PRO</option>
      <option value="3028">Icom IC-761</option>
      <option value="3029">Icom IC-765</option>
      <option value="3030">Icom IC-775</option>
      <option value="3031">Icom IC-781</option>
      <option value="3032">Icom IC-820H</option>
      <option value="3034">Icom IC-821H</option>
      <option value="3035">Icom IC-970</option>
      <option value="3036">Icom IC-R10</option>
      <option value="3037">Icom IC-R71</option>
      <option value="3038">Icom IC-R72</option>
      <option value="3039">Icom IC-R75</option>
      <option value="3040">Icom IC-R7000</option>
      <option value="3041">Icom IC-R7100</option>
      <option value="3042">Icom ICR-8500</option>
      <option value="3043">Icom IC-R9000</option>
      <option value="3044">Icom IC-910</option>
      <option value="3045">Icom IC-78</option>
      <option value="3046">Icom IC-746PRO</option>
      <option value="3047">Icom IC-756PROII</option>
      <option value="3051">Ten-Tec Omni VI Plus</option>
      <option value="3052">Optoelectronics OptoScan535</option>
      <option value="3053">Optoelectronics OptoScan456</option>
      <option value="3054">Icom IC ID-1</option>
      <option value="3055">Icom IC-703</option>
      <option value="3056">Icom IC-7800</option>
      <option value="3057">Icom IC-756PROIII</option>
      <option value="3058">Icom IC-R20</option>
      <option value="3060">Icom IC-7000</option>
      <option value="3061">Icom IC-7200</option>
      <option value="3062">Icom IC-7700</option>
      <option value="3063">Icom IC-7600</option>
      <option value="3064">Ten-Tec Delta II</option>
      <option value="3065">Icom IC-92D</option>
      <option value="3066">Icom IC-R9500</option>
      <option value="3067">Icom IC-7410</option>
      <option value="3068">Icom IC-9100</option>
      <option value="3069">Icom IC-RX7</option>
      <option value="3070">Icom IC-7100</option>
      <option value="3071">Icom ID-5100</option>
      <option value="3072">Icom IC-2730</option>
      <option value="3073">Icom IC-7300</option>
      <option value="3074">Microtelecom Perseus</option>
      <option value="3075">Icom IC-785x</option>
      <option value="3076">Xeigu X108G</option>
      <option value="3077">Icom IC-R6</option>
      <option value="3078">Icom IC-7610</option>
      <option value="3079">Icom IC-R8600</option>
      <option value="3080">Icom IC-R30</option>
      <option value="3081">Icom IC-9700</option>
      <option value="3082">Icom ID-4100</option>
      <option value="3083">Icom ID-31</option>
      <option value="3084">Icom ID-51</option>
      <option value="3085">Icom IC-705</option>
      <option value="4001">Icom IC-PCR1000</option>
      <option value="4002">Icom IC-PCR100</option>
      <option value="4003">Icom IC-PCR1500</option>
      <option value="4004">Icom IC-PCR2500</option>
      <option value="5001">AOR AR8200</option>
      <option value="5002">AOR AR8000</option>
      <option value="5003">AOR AR7030</option>
      <option value="5004">AOR AR5000</option>
      <option value="5005">AOR AR3030</option>
      <option value="5006">AOR AR3000A</option>
      <option value="5008">AOR AR2700</option>
      <option value="5013">AOR AR8600</option>
      <option value="5014">AOR AR5000A</option>
      <option value="5015">AOR AR7030 Plus</option>
      <option value="5016">AOR SR2200</option>
      <option value="6005">JRC NRD-525</option>
      <option value="6006">JRC NRD-535D</option>
      <option value="6007">JRC NRD-545 DSP</option>
      <option value="8001">Uniden BC780xlt</option>
      <option value="8002">Uniden BC245xlt</option>
      <option value="8003">Uniden BC895xlt</option>
      <option value="8004">Radio Shack PRO-2052</option>
      <option value="8006">Uniden BC250D</option>
      <option value="8010">Uniden BCD-396T</option>
      <option value="8011">Uniden BCD-996T</option>
      <option value="8012">Uniden BC898T</option>
      <option value="9002">Drake R-8A</option>
      <option value="9003">Drake R-8B</option>
      <option value="10004">Lowe HF-235</option>
      <option value="11003">Racal RA6790/GM</option>
      <option value="11005">Racal RA3702</option>
      <option value="12004">Watkins-Johnson WJ-8888</option>
      <option value="14002">Skanti TRP8000</option>
      <option value="14004">Skanti TRP 8255 S R</option>
      <option value="15001">Winradio WR-1000</option>
      <option value="15002">Winradio WR-1500</option>
      <option value="15003">Winradio WR-1550</option>
      <option value="15004">Winradio WR-3100</option>
      <option value="15005">Winradio WR-3150</option>
      <option value="15006">Winradio WR-3500</option>
      <option value="15007">Winradio WR-3700</option>
      <option value="15009">Winradio WR-G313</option>
      <option value="16001">Ten-Tec TT-550</option>
      <option value="16002">Ten-Tec TT-538 Jupiter</option>
      <option value="16003">Ten-Tec RX-320</option>
      <option value="16004">Ten-Tec RX-340</option>
      <option value="16005">Ten-Tec RX-350</option>
      <option value="16007">Ten-Tec TT-516 Argonaut V</option>
      <option value="16008">Ten-Tec TT-565 Orion</option>
      <option value="16009">Ten-Tec TT-585 Paragon</option>
      <option value="16011">Ten-Tec TT-588 Omni VII</option>
      <option value="16012">Ten-Tec RX-331</option>
      <option value="16013">Ten-Tec TT-599 Eagle</option>
      <option value="17001">Alinco DX-77</option>
      <option value="17002">Alinco DX-SR8</option>
      <option value="18001">Kachina 505DSP</option>
      <option value="22001">TAPR DSP-10</option>
      <option value="23001">Flex-radio SDR-1000</option>
      <option value="23003">DTTS Microwave Society DttSP IPC</option>
      <option value="23004">DTTS Microwave Society DttSP UDP</option>
      <option value="24001">RFT EKD-500</option>
      <option value="25001">Elektor Elektor 3/04</option>
      <option value="25002">SAT-Schneider DRT1</option>
      <option value="25003">Coding Technologies Digital World Traveller</option>
      <option value="25006">AmQRP DDS-60</option>
      <option value="25007">Elektor Elektor SDR-USB</option>
      <option value="25008">mRS miniVNA</option>
      <option value="25009">SoftRock Si570 AVR-USB</option>
      <option value="25011">KTH-SDR kit Si570 PIC-USB</option>
      <option value="25012">FiFi FiFi-SDR</option>
      <option value="25013">AMSAT-UK FUNcube Dongle</option>
      <option value="25014">N2ADR HiQSDR</option>
      <option value="25015">Funkamateur FA-SDR</option>
      <option value="25016">AE9RB Si570 Peaberry V1</option>
      <option value="25017">AE9RB Si570 Peaberry V2</option>
      <option value="25018">AMSAT-UK FUNcube Dongle Pro+</option>
      <option value="25019">HobbyPCB RS-HFIQ</option>
      <option value="26001">Video4Linux SW/FM radio</option>
      <option value="26002">Video4Linux2 SW/FM radio</option>
      <option value="27001">Rohde&Schwarz ESMC</option>
      <option value="27002">Rohde&Schwarz EB200</option>
      <option value="27003">Rohde&Schwarz XK2100</option>
      <option value="28001">Philips/Simoco PRM8060</option>
      <option value="29001">ADAT www.adat.ch ADT-200A</option>
      <option value="30001">Icom IC-M700PRO</option>
      <option value="30002">Icom IC-M802</option>
      <option value="30003">Icom IC-M710</option>
      <option value="30004">Icom IC-M803</option>
      <option value="31001">Dorji DRA818V</option>
      <option value="31002">Dorji DRA818U</option>
      <option value="32001">Barrett 2050</option>
      <option value="32002">Barrett 950</option>
      <option value="33001">ELAD FDM-DUO</option>
    </select>
  </div>

  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Radio port</span>

    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="hamlib_deviceport"
      style="width: 7rem"
      @change="onChange"
      v-model="settings.remote.RADIO.serial_port"
    >
      <option
        v-for="option in serialDeviceOptions()"
        v-bind:value="option.port"
      >
        {{ option.port }}
      </option>
    </select>
  </div>

  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Serial speed</span>

    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="hamlib_serialspeed"
      @change="onChange"
      v-model.number="settings.remote.RADIO.serial_speed"
    >
      <option selected value="ignore">-- ignore --</option>
      <option value="1200">1200</option>
      <option value="2400">2400</option>
      <option value="4800">4800</option>
      <option value="9600">9600</option>
      <option value="14400">14400</option>
      <option value="19200">19200</option>
      <option value="28800">28800</option>
      <option value="38400">38400</option>
      <option value="57600">57600</option>
      <option value="115200">115200</option>
    </select>
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Data bits</span>

    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="hamlib_data_bits"
      @change="onChange"
      v-model.number="settings.remote.RADIO.data_bits"
    >
      <option selected value="ignore">-- ignore --</option>
      <option value="7">7</option>
      <option value="8">8</option>
    </select>
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Stop bits</span>

    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="hamlib_stop_bits"
      @change="onChange"
      v-model.number="settings.remote.RADIO.stop_bits"
    >
      <option selected value="ignore">-- ignore --</option>
      <option value="1">1</option>
      <option value="2">2</option>
    </select>
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Serial handshake</span>

    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="hamlib_handshake"
      @change="onChange"
      v-model="settings.remote.RADIO.serial_handshake"
    >
      <option selected value="ignore">-- ignore --</option>
      <option value="None">None (Default)</option>
    </select>
  </div>

  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">PTT device port</span>
    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="hamlib_ptt_port"
      @change="onChange"
      v-model="settings.remote.RADIO.ptt_port"
    >
      <option selected value="ignore">-- ignore --</option>
    </select>
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">PTT type</span>

    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="hamlib_pttprotocol"
      style="width: 0.5rem"
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
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">DCD</span>

    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="hamlib_dcd"
      style="width: 0.5rem"
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
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">DTR</span>

    <select
      class="form-select form-select-sm"
      aria-label=".form-select-sm"
      id="hamlib_dtrstate"
      style="width: 0.5rem"
      @change="onChange"
      v-model="settings.remote.RADIO.serial_dtr"
    >
      <option selected value="ignore">-- ignore --</option>
      <option value="OFF">OFF</option>
      <option value="ON">ON</option>
    </select>
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px">Rigctld command</span>
    <input
      type="text"
      class="form-control"
      id="hamlib_rigctld_command"
      aria-label="Device Port"
      aria-describedby="basic-addon1"
      disabled
      placeholder="auto populated from above settings"
    />
    <button
      class="btn btn-outline-secondary"
      type="button"
      id="btnHamlibCopyCommand"
    >
      <i id="btnHamlibCopyCommandBi" class="bi bi-clipboard"></i>
    </button>
  </div>
  <div class="input-group input-group-sm mb-1">
    <span class="input-group-text" style="width: 180px"
      >Rigctld custom arguments</span
    >
    <input
      type="text"
      class="form-control"
      placeholder="not typically needed"
      id="hamlib_rigctld_custom_args"
      aria-label="Custom arguments"
      aria-describedby="basic-addon1"
      @change="onChange"
      v-model="settings.remote.RIGCTLD.arguments"
    />
  </div>
</template>
