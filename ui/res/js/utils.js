/**
 * Utility, stand-alone helper functions.
 */

/**
 * Replaces all occurrences of the strings in `replaceArray` with their 
 * corrispondence in the array
 * 
 * @param {Array} replaceArray Array of strings to replace, in the format:
 *    [['replace this', 'with this', global RegExp? true:false], [..., ...]]
 * @returns the string taken as input, where text occurrences are replaced with  
 *    their corrispondence in `replaceArray`.
 */
String.prototype.replaceList = function(replaceArray) {
  let target = this;

  for (const item of replaceArray) {
    if (item.length == 3 && item[2] == true)
      item[0] = new RegExp(item[0], "g");

    target = target.replace(item[0], item[1]);
  }

  return target;
}

/**
 * Decodes an HTML string
 * @param {String} text String containing encoded HTML
 * @returns String containing the decoded HTML
 */
function decodeHTML(text) {
  var textArea = document.createElement('textarea');
  textArea.innerHTML = text;
  return textArea.value;
}

/**
 * Encodes an HTML string
 * @param {String} text String containing plain HTML
 * @returns String containing the encoded HTML
 */
function encodeHTML(text) {
  var textArea = document.createElement('textarea');
  textArea.innerText = text;
  return textArea.innerHTML;
}

function timestampToDate(unixTimestamp) {
  const date = new Date(unixTimestamp * 1000);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2,"0");
  const day = String(date.getDate()).padStart(2,"0");
  const hour = String(date.getHours()).padStart(2,"0");
  const minutes = String(date.getMinutes()).padStart(2,"0");
  const seconds = String(date.getSeconds()).padStart(2,"0");

  return `${year}/${month}/${day} ${hour}:${minutes}:${seconds}`
}