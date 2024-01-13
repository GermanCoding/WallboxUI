<script>
import {session} from "../session.js";
import {formatDuration, formatValue, STOP_REASONS, tokenToString} from "@/utils";

export default {
  data() {
    return {
      loading: true,
      error: null,
      sortBy: [],
      simple_headers: [
        {title: "Startzeit", key: "started"},
        {title: "Ladedauer", key: "duration"},
        {title: "Geladene Energie", key: "chargedEnergy"},
        {title: "RFID-Karte", key: "authCard"},
      ],
      extended_headers: [
        {title: "Startzeit", key: "started"},
        {title: "Endzeit", key: "ended"},
        {title: "Ladedauer", key: "duration"},
        {title: "Zählerstand bei Start", key: "energyMeterAtStart"},
        {title: "Geladene Energie", key: "chargedEnergy"},
        {title: "Maximaler Ladestrom", key: "hardwarePowerLimit"},
        {title: "Beendet durch", key: "stopReason"},
        {title: "RFID-Karte", key: "authCard"},
        {title: "Sitzungs-ID", key: "sessionID"},
      ],
      viewMode: "simple",
      raw_data: [],
    }
  },
  methods: {
    fetch() {
      this.loading = true;
      session.sendGetToAPI("charge_sessions/list/").then(response => {
        this.error = null;
        this.raw_data = response.data
      }).catch(error => {
        console.log(error);
        this.error = error;
      }).finally(() => {
        this.loading = false;
      })
    }
  },
  computed: {
    chargeLogItems() {
      let items = [];
      this.raw_data.forEach(function (rawItem) {
        let start = new Date(rawItem.started)
        let end = new Date(rawItem.ended)
        let duration = end - start;
        let token = tokenToString(rawItem.token);
        items.push({
          started: start.toLocaleString(),
          ended: end.toLocaleString(),
          duration: formatDuration(duration),
          hardwarePowerLimit: formatValue(rawItem.hardwareCurrentLimit, "A"),
          energyMeterAtStart: formatValue(rawItem.energyMeterAtStart, "Wh"),
          chargedEnergy: formatValue(rawItem.chargedEnergy, "Wh"),
          stopReason: STOP_REASONS[rawItem.stopReason],
          authCard: token,
          sessionID: rawItem.sessionID,
        })
      });
      return items;
    },
    headers() {
      if (this.viewMode === "extended") {
        return this.extended_headers;
      } else {
        return this.simple_headers;
      }
    }
  },
  mounted() {
    this.fetch();
  },
  updated() {
    this.fetch();
  }
}
</script>

<template>
  <v-container class="fill-height">
    <v-responsive class="align-center fill-height">

      <v-container class="align-center">
        <v-row no-gutters class="justify-end">
          <v-spacer></v-spacer>
          <v-col class="text-right flex-column pa-6">
            <v-btn-toggle
              v-model="viewMode"
              divided
              color="primary"
              mandatory
            >
              <v-btn value="simple">Einfach</v-btn>
              <v-btn value="extended">Erweitert</v-btn>
            </v-btn-toggle>
          </v-col>
        </v-row>
      </v-container>

      <v-data-table
        :headers="headers"
        :items="chargeLogItems"
        :sort-by="[]"
        :loading="loading"
        multi-sort
        item-key="sessionID"
        items-per-page="15"
        item-value="sessionID"
      >
      </v-data-table>

      <v-alert v-if="error"
               color="error"
               icon="$error"
               class="my-12"
               variant="tonal"
               :text="error"
      ></v-alert>
    </v-responsive>
  </v-container>
</template>

<script setup>
//
</script>
