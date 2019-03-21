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
          // bar = rectEl;
          // console.log("eventListener called");
          // console.dir(rectEl);
          let conName = rectEl.attributes["title"].textContent;
          changeDetails(conName);
      });
    });
}
