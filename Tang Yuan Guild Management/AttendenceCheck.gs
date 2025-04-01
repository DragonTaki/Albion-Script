/*----- ----- ----- -----*/
// AttendanceCheck.gs
// For Albion Online "Tang Yuan" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/04/02
// Version: v4.1
/*----- ----- ----- -----*/

function attendanceCheck() {
  // Variables for user
  var sheetName = "Master";
  //var sheetName = "Copy of Master";
  var forceMarkNotInGuild = "Not guild member (Force mark)";
  var inGuildYes = ["MC", "TY"];
  var inGuildNo = "❌";
  var attendanceNoData = "No data";

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(sheetName);
  if (!sheet) {
    msgLogger(`Sheet "${sheetName}" not found.`, "e");
    return;
  }
  var lastCol = sheet.getLastColumn();
  var lastRow = sheet.getLastRow();

  if (lastRow < 2) {
    msgLogger(`Sheet "${sheetName}" doesn't have enough rows (need >= 2).`, "e");
    return;
  }
  
  // Get column indexes based on column titles
  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  var columnNames = ["Player", "Guild", "Past 7 Days", "Past 14 Days", "Past 28 Days", "Comment", "Force Mark"];
  var indexes = columnNames.map(name => headers.indexOf(name) + 1);
  
  // Check if any required column is missing
  if (indexes.includes(0)) {
    msgLogger(`Missing required columns: ${columnNames.filter((_, i) => indexes[i] === 0).join(", ")}.`, "e");
    return;
  }
  
  // Extract individual column indexes
  var [playerIndex, inGuildIndex, past7Index, past14Index, past28Index, commentIndex, markIndex] = indexes;
  
  // Read existing data in one go to minimize getRange calls
  var dataRange = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();

  // Variables for fetch
  var guildName = ["Malicious Crew", "Tang Yuan"];
  var intervals = [7, 14, 28];
  var minGP = 50;
  var fetchedData = {};

  // Fetch attendance data for each interval, and store in Map for fast lookup
  intervals.forEach(interval => {
    fetchedData[interval] = new Map();

    guildName.forEach(guild => {
      var url = `https://api-east.albionbattles.com/player?guildSearch=${encodeURIComponent(guild)}&interval=${interval}&minGP=${minGP}`;
      var options = {
        "method": "GET",
        "headers": { "Accept": "application/json" },
          "muteHttpExceptions": true
        };
      
      try {
        var response = UrlFetchApp.fetch(url, options);
        if (response.getResponseCode() !== 200) {
          msgLogger(`HTTP response code ${response.getResponseCode()} for guild "${guild}" at ${interval} days.`, "e");
          return;
        }
        var data = JSON.parse(response.getContentText());
        if (!Array.isArray(data)) {
          msgLogger(`Invalid response format for guild "${guild}" at ${interval} days: ${JSON.stringify(data)}`, "e");
          return;
        }
        data.forEach(player => {
          if (player.name && typeof player.battleNumber === "number") {
            if (fetchedData[interval].has(player.name)) {
              fetchedData[interval].set(player.name, fetchedData[interval].get(player.name) + player.battleNumber);
            } else {
              fetchedData[interval].set(player.name, player.battleNumber);
            }
          }
        });
        msgLogger(`Fetched data for guild "${guild}" at ${interval} days.`);
      } catch (error) {
        msgLogger(`Error fetching data for guild "${guild}" at ${interval} days: ${error.message}`, "e");
      }
    });
  });

  // Step 1: Process each player and update attendance records in bulk
  var results7Days = [], results14Days = [], results28Days = [];
  
  dataRange.forEach((row, i) => {
    var playerName = row[playerIndex - 1];
    var playerStatus = row[inGuildIndex - 1];
    var mark = row[markIndex - 1];
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
  var searchText = "Attendance Updated";
  var values = sheet.getDataRange().getValues().flat();
  var index = values.findIndex(text => typeof text === "string" && text.startsWith(searchText + ":"));
  
  if (index !== -1) {
    var rowIndex = Math.floor(index / lastCol) + 1;
    var colIndex = (index % lastCol) + 2;
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
  var now = new Date();
  var timeZone = Session.getScriptTimeZone();
  var timestamp = Utilities.formatDate(now, timeZone, "yyyy/MM/dd HH:mm:ss");

  var prefix = "Info";
  if (level === "e") {
    prefix = "Error";
  } else if (level === "w") {
    prefix = "Warn";
  }

  Logger.log(`${timestamp} [${prefix}] ${message}`);
}
