<script>
import {session} from "../session.js";
import {formatDuration, formatValue, PLUG_STATE, STOP_REASONS, SYSTEM_STATE, TIME_STATUS, tokenToString} from "@/utils";

export default {
  data() {
    return {
      loading: true,
      error: null,
      has_data: false,
      raw_data: [],
    }
  },
  methods: {
    fetch() {
      this.loading = true;
      session.sendGetToAPI("wallboxes/list/").then(response => {
        this.error = null;
        this.raw_data = response.data;
        if (this.raw_data.length > 0) {
          this.has_data = true;
        }
      }).catch(error => {
        console.log(error);
        this.error = error;
      }).finally(() => {
        this.loading = false;
      })
    },
  },
  computed: {
    wallbox() {
      if (!this.has_data) {
        return {};
      }
      let box = this.raw_data[0];
      return {
        product: box.product,
        serial: box.serial,
        firmware: box.firmwareVersion,
        timeStatus: TIME_STATUS[box.timeStatus],
        systemState: SYSTEM_STATE[box.state],
        plugState: PLUG_STATE[box.plug],
      };
    },
  },
  mounted() {
    this.fetch();
  },
}
</script>

<template>
  <v-container class="fill-height">
    <v-responsive>
      <v-container v-if="has_data">
        <v-row>
          <v-col>
            <v-card title="Allgemein">
              <v-card-text>
                <v-row no-gutters>
                  <v-col class="font-weight-bold text-left" cols="2">
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
            <v-card title="Aktueller Status">
              <v-card-text>
                <v-row no-gutters>
                  <v-col class="font-weight-bold text-left" cols="2">
                    Uhrzeit
                  </v-col>
                  <v-col class="font-weight-regular text-right">
                    {{ wallbox.timeStatus }}
                  </v-col>
                </v-row>
                <v-row no-gutters>
                  <v-col class="font-weight-bold text-left" cols="3">
                    Systemstatus
                  </v-col>
                  <v-col class="font-weight-regular text-right">
                    {{ wallbox.systemState }}
                  </v-col>
                </v-row>
                <v-row no-gutters>
                  <v-col class="font-weight-bold text-left" cols="3">
                    Status des Kabels
                  </v-col>
                  <v-col class="font-weight-regular text-right">
                    {{ wallbox.plugState }}
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-responsive>
  </v-container>
</template>

<style scoped>

</style>
