<script>
import {session} from "../session.js";
import {download, formatDuration, formatValue, STOP_REASONS, tokenToString} from "@/utils";

export default {
  data() {
    return {
      exportTokens: null,
      notBefore: null,
      notAfter: null,
      tokens: null,
      exportValid: null,
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
      session.sendGetToAPI("tokens/list/").then(response => {
        this.error = null;
        this.tokens = response.data
      }).catch(error => {
        console.log(error);
        this.error = error;
      }).finally(() => {
      })
    },
    exportLogs() {
      let exportTokenIDs = null;
      if (this.exportTokens) {
        exportTokenIDs = [];
        let tokens = this.tokens;
        this.exportTokens.forEach(function (tokenName) {
          tokens.forEach(function (token) {
            if (tokenToString(token) == tokenName) {
              exportTokenIDs.push(token.id);
            }
          });
        });
      }
      session.sendGetToAPI("charge_sessions/list/", {
        not_before: this.notBefore,
        not_after: this.notAfter,
        tokens: exportTokenIDs ? exportTokenIDs.join() : null,
      }).then(response => {
        download("export.json", JSON.stringify(response.data), "text/json");
      }).catch(error => {
        console.log(error);
        this.error = error;
      }).finally(() => {
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
    },
    selectableTokens() {
      let selectTokens = [];
      if (this.tokens) {
        this.tokens.forEach(function (token) {
          selectTokens.push(tokenToString(token));
        });
      }
      return selectTokens;
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

      <v-form v-model="exportValid" class="mt-5" @submit.prevent="exportLogs()">
        <v-row>
          <v-col class="text-h4" cols="auto">Export</v-col>
          <v-col>
            <v-text-field v-model="notBefore" label="Von" placeholder="dd.mm.yyyy" persistent-placeholder
                          hint="dd.mm.yyyy"></v-text-field>
          </v-col>
          <v-col>
            <v-text-field v-model="notAfter" label="Bis" placeholder="dd.mm.yyyy" persistent-placeholder
                          hint="dd.mm.yyyy"></v-text-field>
          </v-col>
          <v-col>
            <v-combobox
              v-model="exportTokens"
              :items="selectableTokens"
              label="Nur folgende RFID Tokens"
              hint="Leer für alle"
              persistent-hint
              multiple
            ></v-combobox>
          </v-col>
          <v-col>
            <v-btn type="submit">Export</v-btn>
          </v-col>
        </v-row>
      </v-form>

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
