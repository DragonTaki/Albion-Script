/*----- ----- ----- -----*/
// DiscordRoleCheck.gs
// For Albion Online "Malicious Crew" Guild only
// Do not distribute or modified
// Author: DragonTaki (https://github.com/DragonTaki)
// Create Date: 2025/03/08
// Update Date: 2025/03/08
// Version: v1.0
/*----- ----- ----- -----*/

function discordRoleCheck() {
  var token = ""; // "Tang Yuan Assistant" bot token
  var serverId = "1335220045571166279"; // "Tang Yuan" discord ID
  var userAgent = "DiscordBot (https://github.com/DragonTaki, v1.0)"; // Everyone should has their own user agent
  var limit = 100; // limit maximum 1000
  //var url = `https://discord.com/api/v10/guilds/${serverId}/members?limit=${limit}`;
  var proxyUrl = `https://tangyuan-discord-bot.synasaivaltos.workers.dev/proxy/guilds/${serverId}/members?limit=${limit}`;

  // Use get option
  var options = {
    "method": "GET",
    "headers": {
      "Authorization": "Bot " + token,
      "Content-Type": "application/json",
      "User-Agent": userAgent
    },
    "muteHttpExceptions": true
  };

  try {
    // Fetch player list
    var response = UrlFetchApp.fetch(proxyUrl, options);
    var responseCode = response.getResponseCode();
    
    if (responseCode !== 200) {
      Logger.log(`Error: HTTP response code ${responseCode}`);
      return;
    }

    // If needed print this
    var rawResponse = response.getContentText();
    Logger.log(`Raw Response: ${rawResponse}`);

    var data = JSON.parse(rawResponse);

    // Check if data valid
    if (!data || data.length === 0) {
      Logger.log("Error: No data received from API.");
      return;
    } else {
        Logger.log("Successfully fetched discord member list!");
    }
  } catch (error) {
    Logger.log(`Error during discord member list fetch: ${error}`);
  }

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Discord");
  sheet.clear();
  sheet.appendRow(["User ID", "Username", "Nickname", "Roles"]);

  data.forEach(member => {
    var userId = member.user.id;
    var username = member.user.username;
    var nickname = member.nick || "";
    var roles = member.roles.join(", ");
    sheet.appendRow([userId, username, nickname, roles]);
  });

  Logger.log("Discord member list updated!");
}
