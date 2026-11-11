(function () {
  try {
    var q = new URLSearchParams(location.search);
    if (q.get("свой") === "1") localStorage.setItem("свой", "1");
    var свой = localStorage.getItem("свой") === "1";
    var адрес = "https://hse-risk-cdn.netlify.app/v";
    function отправить(данные) {
      данные.me = свой ? "1" : "0";
      fetch(адрес, { method: "POST", keepalive: true, body: JSON.stringify(данные), headers: { "Content-Type": "text/plain" } }).catch(function () {});
    }
    отправить({ p: location.pathname, r: document.referrer, s: screen.width + "x" + screen.height, l: navigator.language });
    window.отметка = function (имя) { отправить({ p: имя, r: location.pathname }); };
  } catch (e) {}
})();
