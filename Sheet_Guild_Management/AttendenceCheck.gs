/*----- ----- ----- -----*/
// AttendanceCheck.gs
// For Albion Online "Malicious Crew" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/04/16
// Version: v4.2
/*----- ----- ----- -----*/

function attendanceCheck() {
  // Variables for user
  const sheetName = "Master";
  //const sheetName = "Copy of Master";
  const forceMarkNotInGuild = "Not guild member (Force mark)";
  const inGuildYes = new Set(["MC", "TY"]);
  const inGuildNo = "❌";
  const attendanceNoData = "No data";

  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) {
    msgLogger(`Sheet "${sheetName}" not found.`, "e");
    return;
  }
  let lastCol = sheet.getLastColumn();
  let lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    msgLogger(`Sheet "${sheetName}" doesn't have enough rows (need >= 2).`, "e");
    return;
  }
  
  // Get column indexes based on column titles
  const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  const columnNames = ["Player", "Guild", "Past 7 Days", "Past 14 Days", "Past 28 Days", "Comment", "Force Mark"];
  const indexes = columnNames.map(name => headers.indexOf(name) + 1);
  
  // Check if any required column is missing
  if (indexes.includes(0)) {
    msgLogger(`Missing required columns: ${columnNames.filter((_, i) => indexes[i] === 0).join(", ")}.`, "e");
    return;
  }
  
  // Extract individual column indexes
  const [playerIndex, inGuildIndex, past7Index, past14Index, past28Index, commentIndex, markIndex] = indexes;
  
  // Read existing data in one go to minimize getRange calls
  const dataRange = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();

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
    const playerName = row[playerIndex - 1];
    let playerStatus = row[inGuildIndex - 1];
    const mark = row[markIndex - 1];
    if (!playerName) return;
    
    if (mark === forceMarkNotInGuild) {
      row[inGuildIndex - 1] = inGuildNo;
      playerStatus = inGuildNo;
    }

    results7Days[i] = playerStatus === inGuildNo ? attendanceNoData : (fetchedData[7]?.get(playerName) || 0);
    results14Days[i] = playerStatus === inGuildNo ? attendanceNoData : (fetchedData[14]?.get(playerName) || 0);
    results28Days[i] = playerStatus === inGuildNo ? attendanceNoData : (fetchedData[28]?.get(playerName) || 0);
  });

  // Step 2: Batch update attendance data
  sheet.getRange(2, past7Index, lastRow - 1).setValues(results7Days.map(v => [v]));
  sheet.getRange(2, past14Index, lastRow - 1).setValues(results14Days.map(v => [v]));
  sheet.getRange(2, past28Index, lastRow - 1).setValues(results28Days.map(v => [v]));
  
  // Update timestamp
  const searchText = "Attendance Updated";
  const values = sheet.getDataRange().getValues().flat();
  const index = values.findIndex(text => typeof text === "string" && text.startsWith(searchText + ":"));
  
  if (index !== -1) {
    const rowIndex = Math.floor(index / lastCol) + 1;
    const colIndex = (index % lastCol) + 2;
    sheet.getRange(rowIndex, colIndex).setValue(Utilities.formatDate(new Date(), "UTC", "dd/MM/yyyy HH:mm"));
    msgLogger(`"${searchText}" timestamp saved at row ${rowIndex}, col ${colIndex}.`);
  } else {
    msgLogger(`"${searchText}" not found in sheet.`, "e");
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
