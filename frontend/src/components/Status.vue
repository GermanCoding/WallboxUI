<script>
import {session} from "../session.js";
import {
  compareTime,
  formatDuration,
  formatkW,
  formatkWh, formatMilliAmpere,
  formatValue,
  PLUG_STATE, STOP_REASONS,
  SYSTEM_STATE,
  TIME_STATUS, tokenToString
} from "@/utils";

export default {
  data() {
    return {
      loading: true,
      error: null,
      has_data: false,
      raw_data: [],
      timers: [],
    }
  },
  methods: {
    fetch() {
      this.loading = true;
      session.sendGetToAPI("wallboxes/list/", null).then(response => {
        this.error = null;
        this.raw_data = response.data;
        if (this.raw_data.length > 0) {
          this.has_data = true;
        } else {
          this.has_data = false;
        }
      }).catch(error => {
        console.log(error);
        this.error = error;
      }).finally(() => {
        this.loading = false;
      })
    },
    tick() {
      if (!this.has_data) {
        return;
      }
      let box = this.raw_data[0];
      box.uptime += 1;
    },
  },
  computed: {
    wallbox() {
      if (!this.has_data) {
        return {};
      }
      let box = this.raw_data[0];
      let currentStart = new Date(box.currentStartTime)
      let isRunning = box.currentEndTime == null;
      let durationRaw = isRunning ? new Date() - currentStart : new Date(box.currentEndTime) - currentStart;
      return {
        product: box.product,
        serial: box.serial,
        firmware: box.firmwareVersion,
        timeStatus: TIME_STATUS[box.timeStatus],
        systemState: SYSTEM_STATE[box.state],
        plugState: PLUG_STATE[box.plug],
        currentChargePower: formatkW(box.currentChargePower),
        currentPowerFactor: formatValue(box.currentPowerFactor, "%"),
        currentSession: formatkWh(box.currentSession),
        currentHardwareLimit: formatMilliAmpere(box.currentHardwareLimit),
        currentEnergyMeterAtStart: formatkWh(box.currentEnergyMeterAtStart),
        currentStartTime: currentStart.toLocaleString(),
        currentDuration: formatDuration(durationRaw),
        currentSessionID: box.currentSessionID,
        currentToken: tokenToString(box.currentToken),
        currentSessionStatus: STOP_REASONS[box.currentSessionStatus],
        isRunning: isRunning,
        energyMeter: formatkWh(box.energyMeter),
        phase1: formatValue(box.phase1_voltage, "V") + " / " + formatValue(box.phase1_current, "A"),
        phase2: formatValue(box.phase2_voltage, "V") + " / " + formatValue(box.phase2_current, "A"),
        phase3: formatValue(box.phase3_voltage, "V") + " / " + formatValue(box.phase3_current, "A"),
        last_update: compareTime(box.lastUpdated),
        uptime: "vor " + formatDuration(box.uptime * 1000)
      };
    },
    sessionTitle() {
      if (this.wallbox.isRunning) {
        return "Aktuelle Sitzung";
      } else {
        return "Letzte Sitzung";
      }
    },
    cols() {
      const {xxl, xl, lg} = this.$vuetify.display
      return (xxl | xl | lg) ? 6 : 12;
    },
  },
  mounted() {
    this.fetch();
    this.timers.push(setInterval(function () {
      this.fetch();
    }.bind(this), 5000));

    this.timers.push(setInterval(function () {
      this.tick();
    }.bind(this), 1000));
  },
  unmounted() {
    this.timers.forEach(function (timer) {
      clearInterval(timer);
    });
    this.timers = [];
  }
}
</script>

<template>
  <v-container class="mt-lg-8 align-center" v-if="has_data">
    <v-row>
      <v-col :cols="cols">
        <v-card prepend-icon="mdi-ev-station" title="Allgemein">
          <v-card-text>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Modell
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.product }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left">
                Seriennummer
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.serial }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left">
                Firmwareversion
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.firmware }}
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col>
        <v-card prepend-icon="mdi-information" title="Aktueller Status">
          <v-card-text>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Systemstatus
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.systemState }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Status des Kabels
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.plugState }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                <v-icon icon="mdi-meter-electric"></v-icon>
                Zählerstand
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.energyMeter }}
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col :cols="cols">
        <v-card prepend-icon="mdi-electric-switch" title="Elektrisch">
          <v-card-text>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Phase 1 (Spannung/Strom)
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.phase1 }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Phase 2 (Spannung/Strom)
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.phase2 }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Phase 3 (Spannung/Strom)
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.phase3 }}
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col>
        <v-card prepend-icon="mdi-clock-time-eight" title="Zeit/Synchronisation">
          <v-card-text>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Status Uhrzeit (Wallbox)
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.timeStatus }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Letzte Kommunikation Oberfläche ↔ Wallbox
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.last_update }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Letzter Neustart der Wallbox
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.uptime }}
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col :cols="cols">
        <v-card prepend-icon="mdi-car-electric" :title="sessionTitle">
          <v-card-text>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Aktuelle Ladeleistung (W)
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.currentChargePower }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Aktuelle Ladeleistung (%)
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.currentPowerFactor }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Aktuelle Sitzung Gesamt
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.currentSession }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Start der Sitzung
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.currentStartTime }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Dauer der Sitzung
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.currentDuration }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Zählerstand bei Start
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.currentEnergyMeterAtStart }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Maximaler Ladestrom
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.currentHardwareLimit }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                RFID Token
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.currentToken }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Sitzungs-ID
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.currentSessionID }}
              </v-col>
            </v-row>
            <v-row no-gutters>
              <v-col class="font-weight-bold text-left" cols="auto">
                Status
              </v-col>
              <v-col class="font-weight-regular text-right">
                {{ wallbox.currentSessionStatus }}
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
  <v-container v-else-if="!loading">
    <v-alert v-if="error"
             color="error"
             icon="$error"
             class="my-12"
             variant="tonal"
             :text="error"
    ></v-alert>
    <v-alert v-else
             color="error"
             icon="$error"
             class="my-12"
             variant="tonal"
             text="Keine Wallbox in der Datenbank. IP Adresse und Kommunikation zwischen Oberfläche und Wallbox prüfen."
    ></v-alert>
  </v-container>
</template>

<style scoped>
</style>
