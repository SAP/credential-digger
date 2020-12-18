/**
 * replaceList - Replaces all occurrences of the strings in `replaceArray` with
 *    their corrispondence in the array
 * 
 * @param {Array} replaceList L'array di stringhe da sostituire, del formato
 *    [['replace me', 'with me', global RegExp? true:false],
 *    [..., ...]]
 *    Es. [['{{to replace}}', 'foo'], ['some', 'bar', true]]
 * @returns the string taken as input, where {{text}} is replaced with its corrispondence
 *    in the `replaceArray`.
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

function decodeHTML(text) {
  var textArea = document.createElement('textarea');
  textArea.innerHTML = text;
  return textArea.value;
}

function encodeHTML(text) {
  var textArea = document.createElement('textarea');
  textArea.innerText = text;
  return textArea.innerHTML;
}