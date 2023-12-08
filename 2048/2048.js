var arr = [];
var move = 0;
var m = 4,
  n = 4;
var score;
init();
var touchstartX, touchendX, touchstartY, touchendY;

window.addEventListener("beforeunload", (event) => {
  if (move !== -1) event.returnValue = true;
});

setInterval(function () {
  check();
}, 1000);
setInterval(function () {
  document.getElementById("score").innerHTML = "Score: " + score.toString();
}, 10);

function init() {
  score = 0;
  var a = getCookie("row");
  if (a !== "") n = parseInt(a);
  else setCookie("row", "4");
  var b = getCookie("col");
  if (b !== "") m = parseInt(b);
  else setCookie("col", "4");
  htmlinit();
  cssinit();
  var i;
  for (i = 0; i < m * n; i++) arr[i] = 0;
  randn();
  update();
}

function htmlinit() {
  var i;
  for (i = 0; i < m * n; i++) {
    var itemx = document.createElement("div");
    itemx.classList.add("item" + i.toString());
    var element = document.getElementsByClassName("grid-container")[0];
    element.appendChild(itemx);
  }
}

function cssinit() {
  var num = 110 * m - 10;
  num = num.toString();
  document.getElementsByClassName("grid-container")[0].style.width = num + "px";
  var sTemplate = [];
  for (i = 0; i < n; i++) sTemplate = sTemplate + "100px ";
  document.getElementsByClassName("grid-container")[0].style.gridTemplateRows =
    sTemplate;
  sTemplate = [];
  for (i = 0; i < m; i++) sTemplate = sTemplate + "100px ";
  document.getElementsByClassName(
    "grid-container"
  )[0].style.gridTemplateColumns = sTemplate;
}

function update() {
  for (i = 0; i < m * n; i++) {
    var item = document.getElementsByClassName("item" + i)[0];
    item.innerHTML = arr[i];
    if (arr[i] === 0) item.innerHTML = "";
    switch (arr[i]) {
      case 0:
        item.style.backgroundColor = "rgba(238,228,218,.35)";
        break;
      case 2:
        item.style.backgroundColor = " #eee4da";
        item.style.color = "#000000";
        break;
      case 4:
        item.style.backgroundColor = "#ede0c8";
        item.style.color = "#000000";
        break;
      case 8:
        item.style.backgroundColor = "#f2b179";
        item.style.color = "#f9f6f2";
        break;
      case 16:
        item.style.backgroundColor = "#f59563";
        item.style.color = "#f9f6f2";
        break;
      case 32:
        item.style.backgroundColor = "#f67c5f";
        item.style.color = "#f9f6f2";
        break;
      case 64:
        item.style.backgroundColor = "#f65e3b";
        item.style.color = "#f9f6f2";
        break;
      case 128:
        item.style.backgroundColor = "#edcf72";
        item.style.color = "#f9f6f2";
        break;
      case 256:
        item.style.backgroundColor = "#edcc61";
        item.style.color = "#f9f6f2";
        break;
      case 512:
        item.style.backgroundColor = "#edc850";
        item.style.color = "#f9f6f2";
        break;
      case 1024:
        item.style.backgroundColor = "#edc22e";
        item.style.color = "#f9f6f2";
        break;
      case 2048:
        item.style.backgroundColor = "#edc22e";
        item.style.color = "#f9f6f2";
        break;
      case 4096:
        item.style.backgroundColor = "#ebb914";
        item.style.color = "#f9f6f2";
        break;
    }
  }
}

window.addEventListener("keydown", (event) => {
  if (event.keyCode === 38 || event.key === "w" || event.key === "W") up();
  if (event.keyCode === 40 || event.key === "s" || event.key === "S") down();
  if (event.keyCode === 37 || event.key === "a" || event.key === "A") left();
  if (event.keyCode === 39 || event.key === "d" || event.key === "D") right();
});

function checkDirection() {
  diffx=Math.abs(touchendX-touchstartX);
  diffy=Math.abs(touchendY-touchstartY);
  if (diffx > diffy) {
    if (touchendX + 30 < touchstartX) {
      left();
    }
    if (touchendX > touchstartX + 30) {
      right();
    }
  } else {
    if (touchendY + 30 < touchstartY) {
      up();
    }
    if (touchendY > touchstartY + 30) {
      down();
    }
  }
}
window.addEventListener("touchstart", (e) => {
  touchstartX = e.changedTouches[0].screenX;
  touchstartY = e.changedTouches[0].screenY;
});

window.addEventListener("touchend", (e) => {
  touchendX = e.changedTouches[0].screenX;
  touchendY = e.changedTouches[0].screenY;
  checkDirection();
});
function left() {
  rotate();
  right();
  rotate();
}
function up() {
  rotate();
  down();
  rotate();
}
function right() {
  move = 0;
  pushright();
  combine1();
  pushright();
  if (move === 1) randn();
  update();
}

function down() {
  move = 0;
  pushdown();
  combine();
  pushdown();
  if (move === 1) randn();
  update();
}

function pushdown() {
  var i, j, k;
  k = 0;
  for (i = 0; i < m; i++) {
    for (j = n - 1; j >= 0; j--) {
      if (arr[m * j + i] === 0) {
        var t = j;
        while (arr[m * t + i] === 0) {
          t--;
          if (t < 0) break;
        }
        if (t < 0) break;
        else {
          for (k = j; k - j + t >= 0; k--) {
            arr[m * k + i] = arr[m * (k - j + t) + i];
            move = 1;
          }
          for (; k >= 0; k--) arr[m * k + i] = 0;
        }
      }
    }
  }
}
function pushright() {
  var i, j, k;
  k = 0;
  for (j = 0; j < n; j++) {
    for (i = m - 1; i >= 0; i--) {
      if (arr[j * m + i] === 0) {
        var t = i;
        while (arr[j * m + t] === 0) {
          t--;
          if (t < 0) break;
        }
        if (t < 0) break;
        else {
          for (k = i; k - i + t >= 0; k--) {
            arr[j * m + k] = arr[j * m + k - i + t];
            move = 1;
          }
          for (; k >= 0; k--) arr[j * m + k] = 0;
        }
      }
    }
  }
}

function randn() {
  var date = new Date();
  var rd = date.getMilliseconds() % (m * n);
  if (arr[rd] !== 0) {
    randn();
    return;
  }
  var num = date.getMilliseconds() % 10;
  if (num === 0) arr[rd] = 4;
  else arr[rd] = 2;
}

function combine() {
  var i,
    j = 0;
  for (i = 0; i < m; i++) {
    j = n - 1;
    for (; j >= 1; j--) {
      if (arr[m * (j - 1) + i] === 0) break;
      if (arr[m * j + i] === arr[m * (j - 1) + i]) {
        arr[m * (j - 1) + i] = 0;
        arr[m * j + i] = 2 * arr[m * j + i];
        score += arr[m * j + i];
        move = 1;
      }
    }
  }
}
function combine1() {
  var i,
    j = 0;
  for (j = 0; j < n; j++) {
    i = m - 1;
    for (; i >= 1; i--) {
      if (arr[m * j + i - 1] === 0) break;
      if (arr[m * j + i] === arr[m * j + i - 1]) {
        arr[m * j + i - 1] = 0;
        arr[m * j + i] = 2 * arr[m * j + i];
        score += arr[m * j + i];
        move = 1;
      }
    }
  }
}
function rotate() {
  var arr1 = [];
  var i, j;
  for (i = 0; i <= m - 1; i++)
    for (j = 0; j <= n - 1; j++)
      arr1[m * j + i] = arr[m * (n - j - 1) + m - 1 - i];
  arr = arr1;
  update();
}

function button() {
  var arr = '<br /> Row:<input id="row"type="number" /><br/>Column:';
  arr =
    arr +
    '<input id="col" type="number" /> <br /><br /> <button onclick="set1()">Submit</button>';
  var item = document.getElementById("setting");
  if (item.innerHTML === "") item.innerHTML = arr;
  else item.innerHTML = "";
}

function set1() {
  var a = document.getElementById("col").value;
  var b = document.getElementById("row").value;
  if (a === "" || a == 0) {
    alert("invalid input");
    return;
  } else if (b === "" || b == 0) {
    alert("invalid input");
    return;
  } else if (a == 1 && b == 1) {
    alert("invalid input");
    return;
  }
  alert(
    "You changed rows to " + b.toString() + "\nand columns to " + a.toString()
  );
  setCookie("row", b.toString());
  setCookie("col", a.toString());
  location.reload();
}

function check() {
  update();
  if (move === -1) return;
  for (i = 0; i < m; i++)
    for (j = 0; j < n; j++) {
      if (arr[m * j + i] === 0) return;
      if (i + 1 < m) if (arr[m * j + i] === arr[m * j + i + 1]) return;
      if (j + 1 < n) if (arr[m * j + i] === arr[m * (j + 1) + i]) return;
    }
  move = -1;
  alert("Game Over");
  setnamecookie();
  alert("Try Again");
  location.reload();
}
function setnamecookie() {
  var person = prompt(
    "You got " + score + " points\n" + "Please enter your name",
    "Player"
  );
  if (person === null) {
    person = "Player";
  }
  var za = " ".repeat(25);
  var x = new Date();
  var y =
    x.getFullYear().toString() +
    "/" +
    (x.getMonth() + 1).toString() +
    "/" +
    x.getDate().toString() +
    "   " +
    x.getHours().toString() +
    ":" +
    x.getMinutes().toString() +
    ":" +
    x.getSeconds().toString();
  var board = m.toString() + "x" + n.toString();
  person = person.substring(0, 15);
  setCookie(
    x,
    "и" +
      person.substring(0, 15) +
      za.substring(person.length, 16) +
      y +
      za.substring(y.length, 25) +
      board.substring(0, 10) +
      za.substring(board.length, 10) +
      score.toString().substring(0, 10) +
      "и"
  );
}
function setCookie(cname, cvalue) {
  var d = new Date();
  d.setTime(d.getTime() + 1000000000000000);
  var expires = "expires=" + d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
  var name = cname + "=";
  var ca = document.cookie.split(";");
  for (var i = 0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == " ") c = c.substring(1, c.length);
    if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
  }
  return "";
}

function getscores() {
  var x = document.cookie;
  var x = x.split("и");
  var str = "";
  for (var i = 1; i < x.length; i += 2) {
    str = str + x[i] + "\n";
  }
  alert("Scores\n"+str);
}
