/*----- ----- ----- -----*/
// ValueBar.gs
// For Albion Online "Malicious Crew" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/12
// Update Date: 2025/04/16
// Version: v2.0
/*----- ----- ----- -----*/

function increase10() {
  adjustValue("10", 1);
}

function decrease10() {
  adjustValue("10", -1);
}

function increase11() {
  adjustValue("11", 1);
}

function decrease11() {
  adjustValue("11", -1);
}

function increase12() {
  adjustValue("12", 1);
}

function decrease12() {
  adjustValue("12", -1);
}

function adjustValue(rowNumber, change) {
  // Variables for user
  const attendanceText = "--- Attendance Marked Below ---";

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();
  let markerColumnIndex = -1;

  for (let r = 0; r < values.length; r++) {
    for (let c = 0; c < values[r].length; c++) {
      if (
        typeof values[r][c] === "string" &&
        values[r][c].trim().toLowerCase() === attendanceText.toLowerCase()
      ) {
        markerColumnIndex = c;
        break;
      }
    }
    if (markerColumnIndex !== -1) break;
  }
  if (markerColumnIndex === -1) {
    msgLogger(`"${attendanceText}" not found in sheet.`, "e");
    return;
  }
  
  const row = Number(rowNumber);
  const targetCell = sheet.getRange(row, markerColumnIndex + 2);
  let currentValue = targetCell.getValue();
  const maximum = 50;
  const minimum = 0;

  // If not number, set to 0
  if (typeof currentValue !== "number") {
    currentValue = 0;
  }

  let newValue = currentValue + change;
  if (newValue > maximum) newValue = maximum;
  if (newValue < minimum) newValue = minimum;

  targetCell.setValue(newValue);
}

/**
 * Log messages with timestamps and different severity levels.
 * If level is "e", logs as error.
 * If level is "w", logs as warning.
 * If level is omitted, logs as info.
 * @param {string} message - The message to log.
 * @param {string} [level] - The severity level.
 */
function msgLogger(message, level) {
  const timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy/MM/dd HH:mm:ss");
  let prefix = "Info";
  if (level === "e") {
    prefix = "Error";
  } else if (level === "w") {
    prefix = "Warn";
  }

  Logger.log(`${timestamp} [${prefix}] ${message}`);
}
