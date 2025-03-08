/*----- ----- ----- -----*/
// Attendance Check
// For Albion Online "Tang Yuan" Guild only
// Do not distribute or modified
// Author: DragonTaki(https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/03/08
// Version: v1.2
/*----- ----- ----- -----*/

function attendanceCheck() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Master');
  
  // Get player names (Column A)
  var playerNames = sheet.getRange('A2:A' + sheet.getLastRow()).getValues();
  
  // Get if in guild (Column B)
  var inGuild = sheet.getRange('B2:B' + sheet.getLastRow()).getValues();

  // Attendance 7/14/28 days (Column D/E/F)
  var attendance7DaysColumn = sheet.getRange('D2:D' + sheet.getLastRow());
  var attendance14DaysColumn = sheet.getRange('E2:E' + sheet.getLastRow());
  var attendance28DaysColumn = sheet.getRange('F2:F' + sheet.getLastRow());
  attendance7DaysColumn.clearContent();
  attendance14DaysColumn.clearContent();
  attendance28DaysColumn.clearContent();

  // Variables
  var guildName = 'Tang Yuan';
  var results7Days = [];
  var results14Days = [];
  var results28Days = [];
  var intervals = [7, 14, 28]; // Web accept query 7/14/28 days
  var minGP = 10;              // Web accept query 0/10/20/50/100 guild players
  // minGP means only those with more than 10 guild players are counted in the attendance

  intervals.forEach(function(interval) {
    // URL Query
    var url = `https://api-east.albionbattles.com/player?guildSearch=${encodeURIComponent(guildName)}&interval=${interval}&minGP=${minGP}`;

    // Use get option
    var options = {
      "method": "GET",
      "headers": {
        "Accept": "application/json, text/plain, */*"
      },
      "muteHttpExceptions": true
    };

    try {
      // Fetch attendance
      var response = UrlFetchApp.fetch(url, options);
      var responseCode = response.getResponseCode();
      
      if (responseCode !== 200) {
        Logger.log(`Error: HTTP response code ${responseCode}`);
        return;
      }

      // If needed print this
      var rawResponse = response.getContentText();
      //Logger.log(`Raw Response for interval ${interval}: ${rawResponse}`);

      var data = JSON.parse(rawResponse);
      
      // Check if data valid
      if (!Array.isArray(data)) {
        Logger.log(`Invalid response format, expected array: ${JSON.stringify(data)}`);
        return;
      } else {
        Logger.log("Successfully fetched attendance data!");
      }
    } catch (error) {
      Logger.log(`Error during attendance fetch: ${error}`);
    }

    // Check each players
    playerNames.forEach(function(row, index) {
      var playerName = row[0];
      var playerStatus = inGuild[index][0];  // Adjust if player in guild
      if (playerName) {  // If player ID empty
        var playerData = null;
        for (var i = 0; i < data.length; i++) {
          if (data[i].name === playerName) {
            playerData = data[i];
            break;
          }
        }

        if (playerStatus === 'Yes') {
          // If player in guild,
          if (playerData) {
            // If has data, than get attendance
            var attendanceCount = playerData.battleNumber || 0;  // default 0
            if (interval === 7) results7Days.push(attendanceCount);
            if (interval === 14) results14Days.push(attendanceCount);
            if (interval === 28) results28Days.push(attendanceCount);
          } else {
            // If no data, means no attendance, write "0"
            if (interval === 7) results7Days.push(0);
            if (interval === 14) results14Days.push(0);
            if (interval === 28) results28Days.push(0);
          }
        } else if (playerStatus === 'No') {
          // If player NOT in guild,
          if (playerData) {
            // If has data, than get old attendance (before they left)
            var attendanceCount = playerData.battleNumber || 0;
            if (interval === 7) results7Days.push(attendanceCount);
            if (interval === 14) results14Days.push(attendanceCount);
            if (interval === 28) results28Days.push(attendanceCount);
          } else {
            // If no data, just write "No data"
            if (interval === 7) results7Days.push('No data');
            if (interval === 14) results14Days.push('No data');
            if (interval === 28) results28Days.push('No data');
          }
        }
      }
    });
  });

  // Save to sheet
  attendance7DaysColumn.setValues(results7Days.map(function(value) { return [value]; }));
  attendance14DaysColumn.setValues(results14Days.map(function(value) { return [value]; }));
  attendance28DaysColumn.setValues(results28Days.map(function(value) { return [value]; }));

  // Save updated timestamp
  var searchText = "Attendance Updated:";
  var currentDate = new Date();
  var formattedDate = Utilities.formatDate(currentDate, "UTC", "dd/MM/yyyy HH:mm");
  var range = sheet.getDataRange();
  var values = range.getValues();
  var rowIndex = -1;
  var colIndex = -1;

  for (var row = 0; row < values.length; row++) {
    for (var col = 0; col < values[row].length; col++) {
      if (values[row][col] === searchText) {
        rowIndex = row + 1; // Google Sheet index start from 1
        colIndex = col + 2; // Write down right cell
        break;
      }
    }
    if (rowIndex !== -1) break;
  }

  if (rowIndex !== -1 && colIndex !== -1) {
    sheet.getRange(rowIndex, colIndex).setValue(formattedDate);
    Logger.log("Attendance Updated timestamp saved at row " + rowIndex + ", col " + colIndex);
  } else {
    Logger.log(`Error: "${searchText}" not found in sheet.`);
  }

  Logger.log("Attendance data saved!");
}
