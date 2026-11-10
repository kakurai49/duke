"use strict";

// Progressive enhancement only: every record remains readable without scripts.
(() => {
  const controls = document.querySelector("[data-enhanced]");
  const search = document.querySelector("[data-search-input]");
  const records = Array.from(document.querySelectorAll("[data-record]"));
  const count = document.querySelector("[data-result-count]");
  const empty = document.querySelector("[data-empty]");
  if (!controls || !search || !count || !empty) return;

  const filters = Array.from(document.querySelectorAll("[data-filter]"));
  let selected = "all";
  const normalize = (text) => text.normalize("NFKC").toLocaleLowerCase("ja-JP").trim();

  function update() {
    const query = normalize(search.value);
    let visible = 0;
    records.forEach((record) => {
      const group = record.dataset.group;
      const matchesGroup = selected === "all" || group === selected ||
        (selected === "open" && group !== "closed");
      const matchesText = normalize(record.dataset.search || "").includes(query);
      record.hidden = !(matchesGroup && matchesText);
      if (!record.hidden) visible += 1;
    });
    filters.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.filter === selected));
    });
    count.textContent = visible === records.length ? `${visible}件の学び` : `${records.length}件中 ${visible}件`;
    empty.hidden = visible !== 0;
  }

  filters.forEach((button) => {
    button.addEventListener("click", () => {
      selected = button.dataset.filter || "all";
      update();
    });
  });
  search.addEventListener("input", update);
  const reset = document.querySelector("[data-reset]");
  if (reset) {
    reset.addEventListener("click", () => {
      selected = "all";
      search.value = "";
      update();
      search.focus();
    });
  }
  controls.hidden = false;
  update();
})();
