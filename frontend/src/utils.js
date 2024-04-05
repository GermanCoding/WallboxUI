import humanizeDuration from "humanize-duration";

export function download(filename, content, format) {
  let element = document.createElement('a');
  element.setAttribute('href', 'data:' + format + ';charset=utf-8,' + encodeURIComponent(content));
  element.setAttribute('download', filename);

  element.style.display = 'none';
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}

export function formatValue(value, unit) {
  return (value / 1) + " " + unit;
}

export function formatkW(value) {
  return ((value / 1000).toPrecision(4) / 1) + " kW";
}

export function formatkWh(value) {
  return ((value / 1000).toPrecision(4) / 1) + " kWh";
}

export function formatMilliAmpere(value) {
  return ((value / 1000).toPrecision(4) / 1) + " A";
}

export function formatDuration(duration) {
  let units = ["h", "m", "s"];
  if (duration > (24 * 60 * 60 * 1000)) {
    units = ["d", "h", "m"];
  }
  return humanizeDuration(duration, {units: units, language: "de", round: true, maxDecimalPoints: 0});
}

export function compareTime(timestamp) {
  let now = new Date()
  let end = new Date(timestamp)
  if (now > end) {
    return "vor " + formatDuration(now - end);
  } else {
    return "in " + formatDuration(end - now);
  }
}

export function tokenToString(token) {
  if (token.name) {
    return token.name;
  } else {
    return token.tokenID + "/" + token.tokenClass;
  }
}

export const STOP_REASONS = {
  SESSION_RUNNING: "Ladesitzung läuft noch",
  SESSION_CABLE_UNPLUGGED: "Kabel entfernt",
  SESSION_CARD_DEAUTH: "RFID-Karte",
  SESSION_STATUS_UNKNOWN: "Unbekannt",
}


export const TIME_STATUS = {
  UC_TQ_NONE: "Nicht eingestellt (keine Informationen)",
  UC_TQ_NOT_SYNCED: "Nicht korrekt (Standardeinstellungen)",
  UC_TQ_WEAK: "Uhrzeit eingestellt, aber die Genauigkeit ist unbekannt",
  UC_TQ_STRONG: "Mit Zeitserver synchronisiert",
  UC_TQ_UNKNOWN: "Unbekannt"
}

export const SYSTEM_STATE = {
  STATE_STARTUP: "Startet",
  STATE_NOT_READY: "Nicht bereit: nicht autorisiert/nicht verbunden",
  STATE_READY: "Bereit zum laden, wartet auf Fahrzeug",
  STATE_CHARGING: "Lädt",
  STATE_ERROR: "Ein Fehler ist aufgetreten",
  STATE_INTERRUPTED: "Temporärer Fehler (ggf. neu verbinden/neu autorisieren)",
  STATE_UNKNOWN: "Unbekannt",
}

export const PLUG_STATE = {
  PLUG_CABLE_UNPLUGGED: "Kein Kabel (aufseiten der Wallbox) verbunden",
  PLUG_CABLE_UNLOCKED_NOT_CONNECTED: "Kabel in Wallbox eingesteckt, aber nicht mit Fahrzeug verbunden oder verriegelt",
  PLUG_CABLE_LOCKED_NOT_CONNECTED: "Kabel in Wallbox eingesteckt und verriegelt, aber nicht mit Fahrzeug verbunden",
  PLUG_CABLE_CONNECTED_UNLOCKED: "Kabel beidseitig verbunden, aber nicht verriegelt",
  PLUG_CABLE_CONNECTED_LOCKED: "Kabel beidseitig verbunden und verriegelt",
  PLUG_CABLE_UNKNOWN: "Unbekannt"
}
