/* Usage:
   Include this in your SVG document, and then invoke it using something like:

   setupConstituencyDetails("constituency-details", ".constituency")
*/

function setupConstituencyDetails(conDetailId, conSelector) {
    var conDetails = document.getElementById(conDetailId);

    function changeDetails(txt) {
        conDetails.innerHTML = txt;
    }    // conDetails.innerHTML = "Changed by JavaScript";

    changeDetails("This is from changeDetails");

    let conEls = document.querySelectorAll(conSelector);
    // console.log(foo.length);

    conEls.forEach((rectEl) => {
      // console.log("hello");
      rectEl.addEventListener('mouseover', (ev) => {
          let targetEl = ev.target;
          // Ignore elements which are invisible (possibly controlled by
          // parent containing <g> element
          // TODO: verify cascade works if we have overlaid items
          let parentEl = targetEl.parentElement;
          if (targetEl.classList.contains("invisible") ||
              parentEl.classList.contains("invisible")) {
              return;
          }
          // bar = rectEl;
          // console.log("eventListener called");
          // console.dir(rectEl);
          let conName = rectEl.attributes["title"].textContent;
          changeDetails(conName);
      });
    });
}
