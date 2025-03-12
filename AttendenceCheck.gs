/*----- ----- ----- -----*/
// Attendance Check
// For Albion Online "Tang Yuan" Guild only
// Do not distribute or modify
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/07
// Update Date: 2025/03/12
// Version: v2.1
/*----- ----- ----- -----*/

function attendanceCheck() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Master");
  
  // Get column indexes based on column titles
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  // Column headers
  var columnNames = ["Player", "In Guild", "Past 7 Days", "Past 14 Days", "Past 28 Days", "Comment", "Mark"];
  // Get column indexes based on column titles
  var indexes = columnNames.map(name => headers.indexOf(name) + 1);

  // Check if any required column is missing
  var missingColumns = columnNames.filter((name, index) => indexes[index] === 0);
  if (missingColumns.length > 0) {
    Logger.log(`Error: The following required columns are missing: ${missingColumns.join(", ")}`);
    return;
  }

  // Extract individual column indexes
  var playerIndex = indexes[0]; 
  var inGuildIndex = indexes[1];
  var past7Index = indexes[2];
  var past14Index = indexes[3];
  var past28Index = indexes[4];
  var commentIndex = indexes[5];
  var markIndex = indexes[6];

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    Logger.log("No data to process.");
    return;
  }

  // Read existing data
  var playerNames = sheet.getRange(2, playerIndex, lastRow - 1).getValues();
  var inGuildStatus = sheet.getRange(2, inGuildIndex, lastRow - 1).getValues();
  var markStatus = sheet.getRange(2, markIndex, lastRow - 1).getValues();

  // Variables
  var guildName = "Tang Yuan";
  var results7Days = new Array(playerNames.length).fill("No data");
  var results14Days = new Array(playerNames.length).fill("No data");
  var results28Days = new Array(playerNames.length).fill("No data");
  var intervals = [7, 14, 28]; // API accepts queries for 7/14/28 days
  var minGP = 50;              // API accepts minGP values of 0/10/20/50/100

  var fetchedData = {};  

  // Fetch attendance data for each interval
  intervals.forEach(function(interval) {
    var url = `https://api-east.albionbattles.com/player?guildSearch=${encodeURIComponent(guildName)}&interval=${interval}&minGP=${minGP}`;
    
    var options = {
      "method": "GET",
      "headers": {
        "Accept": "application/json, text/plain, */*"
      },
      "muteHttpExceptions": true
    };

    try {
      var response = UrlFetchApp.fetch(url, options);
      var responseCode = response.getResponseCode();
      
      if (responseCode !== 200) {
        Logger.log(`Error: HTTP response code ${responseCode}`);
        return;
      }

      var rawResponse = response.getContentText();
      var data = JSON.parse(rawResponse);
      
      if (!Array.isArray(data)) {
        Logger.log(`Invalid response format, expected array: ${JSON.stringify(data)}`);
        return;
      } else {
        Logger.log(`Successfully fetched attendance data for ${interval} days attendance!`);
      }

      // Store fetched data by interval
      fetchedData[interval] = data;
    } catch (error) {
      Logger.log(`Error during attendance fetch: ${error}`);
    }
  });

  // Process each player
  playerNames.forEach(function(row, index) {
    var playerName = row && row.length > 0 ? row[0] : "";
    var playerStatus = inGuildStatus[index] && inGuildStatus[index].length > 0 ? inGuildStatus[index][0] : "";
    var mark = markStatus[index] && markStatus[index].length > 0 ? markStatus[index][0] : "";
    if (!playerName) return; // Skip empty names
    //Logger.log(`Processing player: ${playerName}`);

    // If marked as "Not guild member", force "In Guild" status to "No"
    if (mark === "Not guild member") {
      sheet.getRange(index + 2, inGuildIndex).setValue("No");
      playerStatus = "No";
    }

    intervals.forEach(function(interval) {
      var playerData = fetchedData[interval]?.find(player => player.name === playerName);
      var attendanceCount = playerData ? (playerData.battleNumber || 0) : 0;

      // If the player is not in the guild, set attendance to "No data"
      if (playerStatus === "No") {
        attendanceCount = "No data";
      }

      if (playerStatus === 'Yes') {
        if (interval === 7) results7Days[index] = attendanceCount;
        if (interval === 14) results14Days[index] = attendanceCount;
        if (interval === 28) results28Days[index] = attendanceCount;
      }
    });

    // Update only if there is a change
    if (sheet.getRange(index + 2, past7Index).getValue() !== results7Days[index]) {
      sheet.getRange(index + 2, past7Index).setValue(results7Days[index]);
    }
    if (sheet.getRange(index + 2, past14Index).getValue() !== results14Days[index]) {
      sheet.getRange(index + 2, past14Index).setValue(results14Days[index]);
    }
    if (sheet.getRange(index + 2, past28Index).getValue() !== results28Days[index]) {
      sheet.getRange(index + 2, past28Index).setValue(results28Days[index]);
    }
  });

  // Save updated timestamp
  var searchText = "Attendance Updated:";
  var currentDate = new Date();
  var formattedDate = Utilities.formatDate(currentDate, "UTC", "dd/MM/yyyy HH:mm");
  var range = sheet.getDataRange();
  var values = range.getValues();
  var rowIndex = -1;
  var colIndex = -1;

  // Find the location of 'Attendance Updated:' in the sheet
  for (var row = 0; row < values.length; row++) {
    for (var col = 0; col < values[row].length; col++) {
      if (values[row][col] === searchText) {
        rowIndex = row + 1;
        colIndex = col + 2;
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
