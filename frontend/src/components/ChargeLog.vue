<script>
import {session} from "../session.js";
import {
  download,
  formatDuration,
  formatkWh,
  formatMilliAmpere,
  formatValue,
  STOP_REASONS,
  tokenToString
} from "@/utils";

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
        {title: "Wallbox", key: "wallboxSerial"}
      ],
      viewMode: "simple",
      raw_data: [],
      wallboxes: [],
    }
  },
  methods: {
    fetch() {
      this.loading = true;
      session.sendGetToAPI("charge_sessions/list/", null).then(response => {
        this.raw_data = response.data
      }).catch(error => {
        console.log(error);
        this.error = error;
      }).finally(() => {
        this.loading = false;
      })
      session.sendGetToAPI("tokens/list/", null).then(response => {
        this.tokens = response.data
      }).catch(error => {
        console.log(error);
        this.error = error;
      }).finally(() => {
      })

      session.sendGetToAPI("wallboxes/list/", null).then(response => {
        this.wallboxes = response.data
      }).catch(error => {
        console.log(error);
        this.error = error;
      }).finally(() => {
      })
    },
    wallboxSerialToProduct(serial) {
      const result = this.wallboxes.find(({box}) => serial === serial);
      if (result) {
        return result.product;
      } else {
        return "Unbekannt";
      }
    },
    exportLogs() {
      if (!this.exportValid) {
        return;
      }
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
        this.error = null;
        let json = response.data;

        let replacer = function (key, value) {
          if (value === null) {
            return '';
          }
          if (typeof value === 'string') {
            // Check if this string is actually a number
            if (value.match(/^[+-]?\d+(?:\.\d+)?$/)) {
              let number = Number(value);
              return number.toLocaleString();
            }
          }
          return value;
        }

        let export_headers = [
          {key: "token", displayName: "RFID Token"},
          {key: "started", displayName: "Beginn"},
          {key: "ended", displayName: "Ende"},
          {key: "chargedEnergy", displayName: "Geladene Energie (Wh)"},
          {key: "wallboxSerial", displayName: "Seriennummer der Wallbox"},
          {key: "wallboxProduct", displayName: "Modell"}
        ];

        for (let i = 0; i < json.length; i++) {
          let element = json[i];
          element['wallboxProduct'] = this.wallboxSerialToProduct(element['wallboxSerial']);
          element['token'] = tokenToString(element['token']);
          for (let key in element) {
            if (!export_headers.some(header => header.key === key)) {
              delete element[key];
            }
          }
        }

        if (json.length < 1) {
          this.error = "Export enthält keine Datensätze.";
          return;
        }

        let fields = Object.keys(json[0]);
        let csv = json.map(function (row) {
          return fields.map(function (fieldName) {
            return JSON.stringify(row[fieldName], replacer)
          }).join(';')
        })
        csv.unshift(fields.map(rawKey => export_headers.find(key => key.key == rawKey).displayName).join(';'))
        csv = csv.join('\r\n');
        let export_filename = "export";
        if (this.notBefore) {
          export_filename += "__" + this.notBefore;
        }
        if (this.notAfter) {
          export_filename += "__" + this.notAfter;
        }
        if (this.exportTokens && this.exportTokens.length) {
          export_filename += "__" + this.exportTokens;
        }
        export_filename += ".csv";
        download(export_filename, csv, "text/csv");
      }).catch(error => {
        console.log(error);
        this.error = error;
      }).finally(() => {
      })
    },
    required(v) {
      return !!v || 'Eingabe erforderlich'
    },
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
          hardwarePowerLimit: formatMilliAmpere(rawItem.hardwareCurrentLimit),
          energyMeterAtStart: formatkWh(rawItem.energyMeterAtStart),
          chargedEnergy: formatkWh(rawItem.chargedEnergy),
          stopReason: STOP_REASONS[rawItem.stopReason],
          authCard: token,
          sessionID: rawItem.sessionID,
          wallboxSerial: rawItem.wallboxSerial
        });
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
    },
  },
  mounted() {
    this.fetch();
  },
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

      <v-form v-model="exportValid" class="mt-5" @submit.prevent="exportLogs()">
        <v-row>
          <v-col class="text-h4" cols="12">Export</v-col>
        </v-row>
        <v-row>
          <v-col class="min-size-date" cols="auto">
            <v-tooltip
              location="top"
              text="Führende Nullen sind nicht erforderlich, andere Zeitformate (z.B. 2024-1-2) funktionieren ebenfalls. Leer für beliebiges Datum."
              open-delay="1500"
              :open-on-click=false
              :open-on-focus=false
              :open-on-hover=true
              close-delay="200"
              :close-on-back=true
              :close-on-content-click=false
            >
              <template v-slot:activator="{ props }">
                <v-text-field v-model="notBefore" label="Von" placeholder="dd.mm.yyyy" persistent-placeholder
                              hint="dd.mm.yyyy" v-bind="props"></v-text-field>
              </template>
            </v-tooltip>
          </v-col>
          <v-col class="min-size-date" cols="auto">
            <v-tooltip
              location="top"
              text="Führende Nullen sind nicht erforderlich, andere Zeitformate (z.B. 2024-1-2) funktionieren ebenfalls. Leer für beliebiges Datum."
              open-delay="1500"
              :open-on-click=false
              :open-on-focus=false
              :open-on-hover=true
              close-delay="200"
              :close-on-back=true
              :close-on-content-click=false
            >
              <template v-slot:activator="{ props }">
                <v-text-field v-model="notAfter" label="Bis" placeholder="dd.mm.yyyy" persistent-placeholder
                              hint="dd.mm.yyyy" v-bind="props"></v-text-field>
              </template>
            </v-tooltip>
          </v-col>
          <v-col class="min-size-tokens">
            <v-combobox
              v-model="exportTokens"
              :items="selectableTokens"
              label="Nur folgende RFID Tokens"
              hint="Leer für alle"
              persistent-hint
              multiple
            ></v-combobox>
          </v-col>
          <v-col cols="auto">
            <v-btn type="submit">Export (CSV)</v-btn>
          </v-col>
        </v-row>
      </v-form>
    </v-responsive>
  </v-container>
</template>

<script setup>
//
</script>

<style scoped>
.min-size-date {
  min-width: 150px;
}

.min-size-tokens {
  min-width: 300px;
}
</style>
