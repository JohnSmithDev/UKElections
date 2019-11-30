/*global Intl:false */
/* Usage:
   Include this in your SVG document, and then invoke it using something like:

   setupConstituencyDetails("constituency-details", ".constituency")
*/

function setupConstituencyDetails(conDetailsContainerId, conSelector) {
    var conDetailsContainer = document.getElementById(conDetailsContainerId);

    function changeDetails(conDetails) {
        const idsAndAttributes = ["constituency",
                                  "electorate-label", "electorate",
                                  "valid-votes-label", "valid-votes",
                                  "turnout-label", "turnout",
                                  "winner-label", "winner", "winner-votes",
                                  "runner-up-label", "runner-up", "runner-up-votes"];
        idsAndAttributes.forEach((x) => {
            conDetailsContainer.querySelector("#" + x).innerHTML = conDetails[x];
        });

        if (conDetails.region === conDetails.country) {
            conDetailsContainer.querySelector("#country-region").innerHTML = conDetails.country;
        } else {
            conDetailsContainer.querySelector("#country-region").innerHTML = conDetails.country + " - " +
                conDetails.region ;
        }
    }

    let conEls = document.querySelectorAll(conSelector);
    // console.log(foo.length);

    conEls.forEach((rectEl) => {
      // console.log("hello");
      rectEl.addEventListener('mouseover', (ev) => {
          let targetEl = ev.target;
          /* Ignore elements which are invisible (possibly controlled by
             parent containing <g> element).  The parent also provides data-
             attributes for country and region */
          // TODO: verify cascade works if we have overlaid items
          let parentEl = targetEl.parentElement;
          if (targetEl.classList.contains("invisible") ||
              parentEl.classList.contains("invisible")) {
              return;
          }
          // bar = rectEl;
          // console.log("eventListener called");
          // console.dir(rectEl);

          function niceInt(n) {
              return new Intl.NumberFormat("en-GB", {style: "decimal"}).format(n);
          }

          let conName = rectEl.attributes["title"].textContent;
          let conAttributes = {
              "region": parentEl.getAttribute("data-region"),
              "country": parentEl.getAttribute("data-country"),
              "constituency": targetEl.getAttribute("title"),

              "electorate-label": "Electorate: ",
              "electorate": niceInt(targetEl.getAttribute("data-electorate")),
              "valid-votes-label": "Valid votes cast: ",
              "valid-votes": niceInt(targetEl.getAttribute("data-valid-votes")),
              "turnout-label": "Turnout: ",
              "turnout": targetEl.getAttribute("data-turnout") + "%",

              "winner-label": "Winning party:",
              "winner": targetEl.getAttribute("data-winner"),
              "winner-votes": niceInt(targetEl.getAttribute("data-winner-votes")) + " votes",
              "runner-up-label": "Runner-up: ",
              "runner-up": targetEl.getAttribute("data-runner-up"),
              "runner-up-votes": niceInt(targetEl.getAttribute("data-runner-up-votes")) + " votes"
          };
          changeDetails(conAttributes);
      });
    });
}
