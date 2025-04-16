/*----- ----- ----- -----*/
// AttendanceCheck.gs
// For Albion Online "Malicious Crew" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/04/17
// Version: v5.0
/*----- ----- ----- -----*/

function attendanceCheck() {
  // Helper Function: Automatically select the sheet (prefer "Copy of ..." if available)
  function getTargetSheet(sheetBaseName) {
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const sheets = spreadsheet.getSheets();
    const copySheet = sheets.find(sheet => sheet.getName().includes(`Copy of ${sheetBaseName}`));
    return copySheet || spreadsheet.getSheetByName(sheetBaseName);
  }

  // Variables for user
  const SHEET_NAME = "Master";
  const FORCE_MARK_IN_GUILD = "Guild member";
  const FORCE_MARK_NOT_IN_GUILD = "Not guild member (Force mark)";
  const GUILD_TAGS = ["MC", "TY"];
  const NOT_IN_GUILD_MARK = "❌";
  const NO_DATA_STRING = "No data";

  // Variables
  const sheet = getTargetSheet(SHEET_NAME);
  if (!sheet) {
    msgLogger(`Sheet "${SHEET_NAME}" not found.`, "e");
    return;
  }
  const lastColumn = sheet.getLastColumn();
  let lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    msgLogger(`Sheet "${SHEET_NAME}" doesn't have enough rows (need >= 2).`, "e");
    return;
  }

  // Read headers
  const headerRow = sheet.getRange(1, 1, 1, lastColumn).getValues()[0];
  
  // Define expected column titles
  const columnTitleMap = {
    player: "Player",
    guild: "Guild",
    past7: "Past 7 Days",
    past14: "Past 14 Days",
    past28: "Past 28 Days",
    comment: "Comment",
    mark: "Force Mark"
  };
  let columns;
  
  // Check if any required column is missing
  try {
    columns = getColumnIndexes(headerRow, columnTitleMap);
  } catch (error) {
    return;
  }

  // Wrap columns to auto -1 when accessing by Proxy
  const columns_ = new Proxy(columns, {
    get: (target, prop) => target[prop] - 1
  });
  
  // Read existing data in one go to minimize getRange calls
  let dataRange = sheet.getRange(2, 1, lastRow - 1, lastColumn).getValues();

  // Variables for fetch
  const guildName = ["Malicious Crew", "Tang Yuan"];
  const intervals = [7, 14, 28];
  const minGP = 50;
  const fetchedData = Object.fromEntries(intervals.map(interval => [interval, new Map()]));

  // Fetch attendance data for each interval, and store in Map for fast lookup
  intervals.forEach(interval => {
    guildName.forEach(guild => {
      const url = `https://api-east.albionbattles.com/player?guildSearch=${encodeURIComponent(guild)}&interval=${interval}&minGP=${minGP}`;
      const options = {
        "method": "GET",
        "headers": { "Accept": "application/json" },
          "muteHttpExceptions": true
        };
      
      try {
        const response = UrlFetchApp.fetch(url, options);
        if (response.getResponseCode() !== 200) {
          msgLogger(`HTTP response code ${response.getResponseCode()} for guild "${guild}" at ${interval} days.`, "e");
          return;
        }
        const data = JSON.parse(response.getContentText());
        if (!Array.isArray(data)) {
          msgLogger(`Invalid response format for guild "${guild}" at ${interval} days: ${JSON.stringify(data)}`, "e");
          return;
        }
        data.forEach(player => {
          if (player.name && typeof player.battleNumber === "number") {
            fetchedData[interval].set(player.name, (fetchedData[interval].get(player.name) || 0) + player.battleNumber);
          }
        });
        msgLogger(`Fetched data for guild "${guild}" at ${interval} days.`);
      } catch (error) {
        msgLogger(`Error fetching data for guild "${guild}" at ${interval} days: ${error.message}`, "e");
      }
    });
  });

  // Step 1: Process each player and update attendance records in bulk
  const results7Days = [], results14Days = [], results28Days = [];
  
  dataRange.forEach((row, i) => {
    const playerName = row[columns_.player];
    let currentGuildStatus = row[columns_.guild];
    const currentMark = row[columns_.mark];
    if (!playerName) return;
    
    if (currentMark === FORCE_MARK_NOT_IN_GUILD) {
      row[columns_.guild] = NOT_IN_GUILD_MARK;
      currentGuildStatus = NOT_IN_GUILD_MARK;
    }

    results7Days[i] = currentGuildStatus === NOT_IN_GUILD_MARK ? NO_DATA_STRING : (fetchedData[7]?.get(playerName) || 0);
    results14Days[i] = currentGuildStatus === NOT_IN_GUILD_MARK ? NO_DATA_STRING : (fetchedData[14]?.get(playerName) || 0);
    results28Days[i] = currentGuildStatus === NOT_IN_GUILD_MARK ? NO_DATA_STRING : (fetchedData[28]?.get(playerName) || 0);
  });

  // Step 2: Batch update attendance data
  sheet.getRange(2, columns.past7, lastRow - 1).setValues(results7Days.map(v => [v]));
  sheet.getRange(2, columns.past14, lastRow - 1).setValues(results14Days.map(v => [v]));
  sheet.getRange(2, columns.past28, lastRow - 1).setValues(results28Days.map(v => [v]));
  
  // Update timestamp
  const SEARCH_TEXT = "Attendance Updated";
  const values = sheet.getDataRange().getValues().flat();
  const index = values.findIndex(text => typeof text === "string" && text.startsWith(SEARCH_TEXT + ":"));
  
  if (index !== -1) {
    const rowIndex = Math.floor(index / lastColumn) + 1;
    const colIndex = (index % lastColumn) + 2;
    sheet.getRange(rowIndex, colIndex).setValue(Utilities.formatDate(new Date(), "UTC", "dd/MM/yyyy HH:mm"));
    msgLogger(`"${SEARCH_TEXT}" timestamp saved at row ${rowIndex}, col ${colIndex}.`);
  } else {
    msgLogger(`"${SEARCH_TEXT}" not found in sheet.`, "e");
  }
  
  msgLogger(`Attendance data updated!`);
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
  const now = new Date();
  const timeZone = Session.getScriptTimeZone();
  const timestamp = Utilities.formatDate(now, timeZone, "yyyy/MM/dd HH:mm:ss");

  let prefix = "Info";
  if (level === "e") {
    prefix = "Error";
  } else if (level === "w") {
    prefix = "Warn";
  }

  Logger.log(`${timestamp} [${prefix}] ${message}`);
}

/**
 * Get indexes of specified column headers
 * @param {string[]} headers - The header row of the sheet
 * @param {Object} nameMap - Mapping of logical names to column titles
 * @returns {Object} - Object with logical names and their 1-based column indexes
 * @throws {Error} - Throws if required column headers are missing
 */
function getColumnIndexes(headers, nameMap) {
  const indexes = {};
  const missing = [];

  for (const key in nameMap) {
    const title = nameMap[key];
    const idx = headers.indexOf(title);
    if (idx === -1) {
      missing.push(title);
    } else {
      indexes[key] = idx + 1; // Convert 0-based to 1-based index
    }
  }

  if (missing.length > 0) {
    msgLogger(`Missing required columns: ${missing.join(", ")}`, "e");
    throw new Error(`Missing required columns.`);
  }

  return indexes;
}
