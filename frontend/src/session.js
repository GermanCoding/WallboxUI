import {reactive} from 'vue'
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE;
const API_ADMIN = import.meta.env.VITE_API_ADMIN;

export const session = reactive({
  _sessionToken: {
    token: localStorage.getItem("session"),
    expiry: localStorage.getItem("session_valid")
  },
  get sessionToken() {
    if (this._sessionToken == null) {
      return null;
    }
    return this._sessionToken.token;
  },
  set sessionToken(value) {
    if (value != null) {
      localStorage.setItem("session", value.token);
      localStorage.setItem("session_valid", value.expiry);
    } else {
      localStorage.removeItem("session");
      localStorage.removeItem("session_valid");
    }
    this._sessionToken = value;
  },
  isLoggedIn() {
    return this.sessionToken != null
  },
  tokenExpiresSoon() {
    if (this._sessionToken == null) {
      return false;
    }
    let expiry = new Date(this._sessionToken.expiry);
    let now = new Date();
    let hour = 1 * 60 * 60 * 1000;
    if ((expiry - now) < hour) {
      return true;
    }
    return false;
  },
  login(username, password) {
    return new Promise(function (resolve, reject) {
      axios.post(API_BASE + "login/", {}, {
        auth: {
          username: username,
          password: password,
        }
      }).then(response => {
        session.sessionToken = response.data;
        resolve();
      }).catch(error => {
        if (error.response != undefined && error.response.data !== undefined && error.response.data.detail !== undefined) {
          reject(error.response.data.detail);
        } else {
          reject(error.toString());
        }
      });
    });
  },
  logout() {
    if (this.isLoggedIn()) {
      // TODO: Give the user a choice between logout (this session only) and logoutall (all sessions of current user)?
      this.sendPostToAPI("logout/", {});
    }
    this.sessionToken = null;
  }
  ,
  sendPostToAPI(request, params) {
    let session_token = this.sessionToken;
    return new Promise(function (resolve, reject) {
      axios.post(API_BASE + request, params, {
        headers: {
          'Authorization': 'Token ' + session_token
        }
      }).then(response => {
        resolve(response)
      }).catch(error => {
        if (session.isLoggedIn()) {
          if (error.response.status == 401 || error.response.status == 403) {
            // Our token is no longer valid
            session.logout();
          }
        }
        if (error.response != undefined && error.response.data !== undefined && error.response.data.detail !== undefined) {
          reject(error.response.data.detail);
        } else {
          reject(error.toString());
        }
      });
    });
  },
  sendGetToAPI(request) {
    let session_token = this.sessionToken;
    return new Promise(function (resolve, reject) {
      axios.get(API_BASE + request, {
        headers: {
          'Authorization': 'Token ' + session_token
        }
      }).then(response => {
        resolve(response)
      }).catch(error => {
        if (session.isLoggedIn()) {
          if (error.response.status == 401 || error.response.status == 403) {
            // Our token is no longer valid
            session.logout();
          }
        }
        if (error.response != undefined && error.response.data !== undefined && error.response.data.detail !== undefined) {
          reject(error.response.data.detail);
        } else {
          reject(error.toString());
        }
      });
    });
  },
  getAdminURL() {
    return API_ADMIN;
  }
})
