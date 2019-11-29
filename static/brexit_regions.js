/* Interactive functionality to support filtering of points by regions/levels */
/* Also the dark mode toggle */
/* TODO: support multiple groups of levels */

function initializeRegionLevels(buttonSelector) {
    let buttonEls = Array.from(document.querySelectorAll(buttonSelector));

    function selectOrUnselectButtons(selectedLevel) {
        let selectedButtonEl = document.querySelector("#js-level-" + selectedLevel);
        // Unselect any other items and select this one
        buttonEls.forEach((el) => { el.classList.remove("selected"); });
        selectedButtonEl.classList.add("selected");
    }

    function makeLevelsVisible(selectedLevel) {
        document.querySelectorAll(".js-level").forEach((el) => {
            let isSelectedLevel = el.classList.contains("level-" + selectedLevel);
            if (selectedLevel === "all" || isSelectedLevel) {
                // el.classList.add("visible");
                el.classList.remove("invisible");
            } else {
                el.classList.add("invisible");
                // el.classList.remove("visible");
            }
        });
    }

    buttonEls.forEach((el) => {
        if (el.classList.contains("selected")) {
            const level = el.getAttribute("data-level");
            makeLevelsVisible(level);
        }
        el.addEventListener("click",
            function levelClickHandler(ev) {
                let clickedEl = ev.target; /* This will be the rect or text, not the group */
                let buttonEl = clickedEl.parentElement; /* The containing <g> */
                const level = buttonEl.getAttribute("data-level");
                // console.log("clicked " + level);

                selectOrUnselectButtons(level);
                makeLevelsVisible(level);
            }
        );
    });
}


initializeRegionLevels(".js-level-button");

document.querySelector('#js-dark-mode-toggle').addEventListener("click",
    function toggleDarkModehandler(ev) {
        document.querySelector("svg").classList.toggle("dark-mode");
    }
);
