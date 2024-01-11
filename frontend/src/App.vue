<script>
import {session} from "./session.js";

const title = "Keba Wallbox Management";

export default {
  data() {
    return {
      drawer: null,
      formValid: false,
      password_visible: false,
      username: null,
      password: null,
      error_text: null,
    }
  },
  methods: {
    login() {
      this.error_text = null;
      session.login(this.username, this.password).then(() => {
        this.username = null;
      }).catch(error => {
        this.error_text = error;
      }).finally(() => {
        this.password = null;
      });
    },
    required(v) {
      return !!v || 'Eingabe erforderlich'
    },
  },
  computed: {
    mobile() {
      return this.$vuetify.display.mobile;
    }
  },
  beforeMount: function () {
    if (session.isLoggedIn() && session.tokenExpiresSoon()) {
      session.logout();
    }
  },
}
</script>

<template>
  <v-app>
    <template v-if="session.isLoggedIn()">
      <v-app-bar v-if="mobile" app>
        <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
        <v-toolbar-title>{{ title }}</v-toolbar-title>
      </v-app-bar>

      <v-navigation-drawer v-model="drawer">
        <v-list-item v-if="!mobile" :title=title subtitle="Demo"></v-list-item>
        <v-divider></v-divider>
        <v-list-item link prepend-icon="mdi-history" title="Ladelog" :to="{ name: 'chargelog'}"></v-list-item>
        <v-list-item link title="Template" :to="{ name: 'template' }"></v-list-item>
        <v-list-item link prepend-icon="mdi-security" title="Admin" :href="session.getAdminURL()"></v-list-item>
        <v-divider></v-divider>
        <v-list-item link prepend-icon="mdi-logout" title="Logout" @click="session.logout()"
                     class="py-3"></v-list-item>
      </v-navigation-drawer>
      <v-main>
        <RouterView/>
      </v-main>
    </template>
    <template v-else>
      <v-main>
        <v-container class="fill-height">
          <v-responsive class="align-center fill-height">
            <v-card
              class="mx-auto pa-12 pb-8"
              elevation="8"
              max-width="448"
              rounded="lg"
            >
              <v-form @submit.prevent="login()" v-model="formValid">
                <div class="text-subtitle-1 text-medium-emphasis">Account</div>
                <v-text-field
                  :rules="[required]"
                  v-model="username"
                  density="compact"
                  placeholder="Benutzername"
                  prepend-inner-icon="mdi-account-outline"
                  variant="outlined"
                ></v-text-field>

                <div class="text-subtitle-1 text-medium-emphasis d-flex align-center justify-space-between">
                  Passwort
                  <a
                    class="text-caption text-decoration-none text-blue"
                    href="#"
                    rel="noopener noreferrer"
                    target="_blank"
                    tabindex="-1"
                  >
                    Passwort vergessen?</a>
                </div>

                <v-text-field
                  v-model="password"
                  :append-inner-icon="password_visible ? 'mdi-eye-off' : 'mdi-eye'"
                  :type="password_visible ? 'text' : 'password'"
                  :rules="[required]"
                  density="compact"
                  placeholder="Passwort eingeben"
                  prepend-inner-icon="mdi-lock-outline"
                  variant="outlined"
                  @click:append-inner="password_visible = !password_visible"
                ></v-text-field>

                <v-card v-if="error_text == null"
                        class="mb-12"
                        color="surface-variant"
                        variant="tonal"
                >
                  <v-card-text class="text-medium-emphasis text-caption">
                    Demo Text. Hier könnte ihr Text stehen (aber keine Werbung!).
                  </v-card-text>
                </v-card>
                <v-alert v-else
                         color="error"
                         icon="$error"
                         class="mb-12"
                         variant="tonal"
                         :text="error_text"
                ></v-alert>

                <v-btn
                  :disabled="!formValid"
                  block
                  class="mb-8"
                  color="blue"
                  size="large"
                  variant="tonal"
                  type="submit"
                >
                  Einloggen
                </v-btn>
              </v-form>
            </v-card>
          </v-responsive>
        </v-container>
      </v-main>
    </template>
  </v-app>
</template>

<script setup>
import {RouterView} from 'vue-router'
import {useDisplay} from 'vuetify'

const {display} = useDisplay()
</script>
