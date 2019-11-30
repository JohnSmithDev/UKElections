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

function showOrHideConstituencyByParty(classesToShow) {
    document.querySelectorAll("#datapoints .constituency").forEach((el) => {
        el.classList.add("invisible");
    });
    classesToShow.forEach((cls) => {
        document.querySelectorAll("#datapoints .constituency." + cls).forEach((el) => {
            el.classList.remove("invisible");
        });
    });
}
function showAllConstituencies() {
    /* Note that level/region hiding may still be in effect */
    document.querySelectorAll("#datapoints .constituency").forEach((el) => {
        el.classList.remove("invisible");
    });
}
function unselectAllPartyFilters() {
    document.querySelectorAll(".legend .constituency").forEach((el) => {
        el.classList.remove("selected");
    });
    document.querySelectorAll(".legend .selectable-party").forEach((el) => {
        el.classList.remove("selected");
    });
}

document.querySelectorAll(".legend .constituency").forEach((el) => {
    el.addEventListener("click",
        function togglePartyWinnerOrRunnerUpHidingListener(ev) {
            let targetEl = ev.target;
            showAllConstituencies(); // Undo any existing filtering
            if (targetEl.classList.contains("selected")) {
                targetEl.classList.remove("selected");
            } else {
                unselectAllPartyFilters();
                let cssClasses = Array.from(targetEl.classList);
                let relevantClass = cssClasses.find((cls) => {
                    if (cls.startsWith("party-") || cls.startsWith("second-place-")) {
                        return cls;
                    } else {
                        return undefined;
                    }
                });
                showOrHideConstituencyByParty([relevantClass]);
                targetEl.classList.add("selected");
            }
        }
    );
});
document.querySelectorAll(".legend .selectable-party").forEach((el) => {
    el.addEventListener("click",
        function togglePartyHidingListener(ev) {
            let targetEl = ev.target;
            showAllConstituencies(); // Undo any existing filtering
            if (targetEl.classList.contains("selected")) {
                targetEl.classList.remove("selected");
            } else {
                unselectAllPartyFilters();
                let party = targetEl.getAttribute("data-party");
                showOrHideConstituencyByParty(["party-" + party,
                                               "second-place-" + party]);
                targetEl.classList.add("selected");
            }
        }
    );
});



initializeRegionLevels(".js-level-button");

document.querySelector('#js-dark-mode-toggle').addEventListener("click",
    function toggleDarkModehandler(ev) {
        document.querySelector("svg").classList.toggle("dark-mode");
    }
);
