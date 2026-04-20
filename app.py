var SHEET_ID = "1WcVWos3p9NJKKEpY2L1-gmKhEkZJH1FL8Hy5bNqHyRA";
var TOKEN = "8215367070:AAF6NgYrM4EsK4E7bM_6iFf-Y_FB3Ni13Es";

function doGet(e) {
  var action = e.parameter.accion;
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName("PEDIDOS"); // <--- ASEGÚRATE QUE LA PESTAÑA SE LLAME ASÍ

  if (action == "nuevo") {
    try {
      sheet.appendRow([
        new Date(), 
        "'" + e.parameter.tel, // Forzamos texto con el apóstrofe para evitar puntos decimales
        e.parameter.nombre, 
        e.parameter.dir, 
        e.parameter.detalle, 
        e.parameter.total, 
        "Pendiente"
      ]);
      return ContentService.createTextOutput("OK");
    } catch (err) {
      return ContentService.createTextOutput("Error: " + err.message);
    }
  }
  return ContentService.createTextOutput("Script Activo");
}

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    if (data.callback_query) {
      var query = data.callback_query;
      var partes = query.data.split("_"); 
      var nuevoEstado = partes[1];
      var dniBuscado = partes[2];
      
      var ss = SpreadsheetApp.openById(SHEET_ID);
      var sheet = ss.getSheetByName("PEDIDOS");
      var datos = sheet.getDataRange().getValues();
      
      for (var i = datos.length - 1; i > 0; i--) {
        // Limpiamos ambos DNIs para comparar solo números
        var dniFila = datos[i][1].toString().replace(/[^\d]/g, "");
        if (dniFila == dniBuscado) {
          sheet.getRange(i + 1, 7).setValue(nuevoEstado); // Columna 7 = G
          break;
        }
      }
      
      // Responder a Telegram para quitar el relojito del botón
      UrlFetchApp.fetch("https://api.telegram.org/bot" + TOKEN + "/answerCallbackQuery", {
        method: "post",
        payload: { callback_query_id: query.id, text: "Estado: " + nuevoEstado }
      });
    }
    return ContentService.createTextOutput("OK");
  } catch(err) {
    return ContentService.createTextOutput("Error");
  }
}

// EJECUTAR ESTA FUNCIÓN UNA VEZ MANUALMENTE
function configurarWebhook() {
  var url = "https://api.telegram.org/bot" + TOKEN + "/setWebhook";
  var webhookUrl = ScriptApp.getService().getUrl();
  var response = UrlFetchApp.fetch(url, {
    method: "post",
    payload: { url: webhookUrl }
  });
  Logger.log(response.getContentText());
}
