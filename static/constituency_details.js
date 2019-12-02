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
                                  "winner-label", "winner", "winner-votes", "winner-percent",
                                  "runner-up-label", "runner-up", "runner-up-votes", "runner-up-percent",
                                  "won-by-label", "won-by-votes",  "won-by-percent"];
        idsAndAttributes.forEach((x) => {
            conDetailsContainer.querySelector("#" + x).innerHTML = conDetails[x];
        });

        if (conDetails.region === conDetails.country) {
            conDetailsContainer.querySelector("#country-region").innerHTML = conDetails.country;
        } else {
            conDetailsContainer.querySelector("#country-region").innerHTML = conDetails.country + " - " +
                conDetails.region ;
        }

        function replacePartyClass(el, newClass) {
            Array.from(el.classList).forEach((cls) => {
                if ((cls.startsWith("party-")) ||
                    (cls.startsWith("winner-")) ||
                    (cls.startsWith("second-place-")) ||
                    (cls.startsWith("runner-up-"))) {
                    el.classList.remove(cls);
                }
                el.classList.remove("invisible"); // Has this at startup
                el.classList.add(newClass);
            });
        }

        replacePartyClass(conDetailsContainer.querySelector("#winner-colour"),
                          conDetails["winner-colour"]);
        replacePartyClass(conDetailsContainer.querySelector("#runner-up-colour"),
                          conDetails["runner-up-colour"]);

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

          function getMatchingPrefixClass(el, classPrefix) {
              return Array.from(el.classList).find((cls) => {
                  if (cls.startsWith(classPrefix)) {
                      return cls;
                  } else {
                      return undefined;
                  }
              });
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
              "winner-colour": getMatchingPrefixClass(targetEl, "party-"),
              "winner": targetEl.getAttribute("data-winner"),
              "winner-votes": niceInt(targetEl.getAttribute("data-winner-votes")) + " votes",
              "winner-percent": "(" + targetEl.getAttribute("data-winner-percent") + "%)",

              "runner-up-label": "Runner-up: ",
              "runner-up-colour": getMatchingPrefixClass(targetEl, "second-place-"),
              "runner-up": targetEl.getAttribute("data-runner-up"),
              "runner-up-votes": niceInt(targetEl.getAttribute("data-runner-up-votes")) + " votes",
              "runner-up-percent": "(" + targetEl.getAttribute("data-runner-up-percent") + "%)",

              "won-by-label": "Won by: ",
              "won-by-votes": niceInt(targetEl.getAttribute("data-winner-votes") -
                  targetEl.getAttribute("data-runner-up-votes")) + " votes",
              "won-by-percent": "(" + targetEl.getAttribute("data-won-by-percent") + "%)"
          };
          changeDetails(conAttributes);
      });
    });
}
