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

// A single page attempt: preserve the first recall separately from later notes.
// Nothing leaves the page. The learner explicitly copies the handoff text.
(() => {
  const page = document.querySelector("[data-learning-practice]");
  if (!page) return;
  const find = (selector) => page.querySelector(selector);
  const recall = find("[data-current-recall]");
  const reference = find("[data-recall-condition]");
  const idea = find("[data-application-idea]");
  const freezeButton = find("[data-freeze-recall]");
  const recallStatus = find("[data-recall-status]");
  const frozenText = find("[data-frozen-recall]");
  const frozenCondition = find("[data-frozen-condition]");
  const note = find("[data-comparison-note]");
  const plan = find("[data-next-practice]");
  const actionStatus = find("[data-practice-status]");
  const result = find("[data-practice-result]");
  const suggestion = find("[data-next-suggestion]");
  const handoff = find("[data-handoff]");
  const selectButton = find("[data-select-handoff]");
  const copyStatus = find("[data-copy-status]");
  const disclosures = Array.from(page.querySelectorAll("[data-answer-disclosure]"));
  const entries = Array.from(page.querySelectorAll("[data-history-entry]"));
  if ([recall, reference, idea, freezeButton, recallStatus, frozenText, frozenCondition,
    note, plan, actionStatus, result, suggestion, handoff, selectButton, copyStatus].some((node) => !node)) return;

  const startedAt = new Date().toISOString();
  let firstRecall = null;
  let exposedAt = null;
  let firstDisclosure = null;
  const references = {
    unknown: "他資料・ヒントの参照有無は未申告",
    no_reference: "本人申告：他資料・ヒントを見ずに書いた",
    referenced: "本人申告：他資料・ヒントを見てから書いた、または途中で見た"
  };
  const comparisons = {
    remembered: "思い出せた",
    missing: "抜けていた",
    different: "食い違う",
    unconfirmed: "当時も未確認・予定だった",
    uncertain: "まだ判断できない"
  };
  const actions = {
    remembered: "思い出せた点を、別の具体例や身近な場面で説明してみる。使えた根拠と、難しかった点を残す。",
    missing: "抜けていた出来事を一つ選び、資料を閉じて自分の言葉で説明する。後日の再想起では参照条件も記録する。",
    different: "食い違う箇所の出典と訂正の経緯を確かめる。過去の記録そのものが誤っている可能性も分けて残す。",
    unconfirmed: "当時も未確認だった点は、忘れたことと分ける。何を観察・質問すれば確かめられるかを一つ決める。",
    uncertain: "判断が難しい点を一つに絞り、どの根拠を確認すれば比較できるかを書く。"
  };
  const executionLabels = {
    not_started: "まだ実施していない",
    in_progress: "取り組んでいる途中",
    reported_done: "実施した（本人申告・達成度は未判定）"
  };

  function selections() {
    return entries.map((entry) => {
      const control = entry.querySelector("[data-comparison]");
      const title = entry.querySelector("[data-entry-title]");
      return { id: entry.dataset.entryId || "", title: title ? title.textContent : "記録",
        value: control ? control.value : "" };
    });
  }

  function update() {
    const selected = selections();
    const selectedActions = selected.filter((entry) => actions[entry.value]);
    suggestion.textContent = selectedActions.length
      ? "次の一歩の候補（必要なものを選んで具体化）：\n" + selectedActions.map((entry) => "・" + entry.title + "：" + actions[entry.value]).join("\n")
      : "記録を見比べて、上の選択欄で差を選ぶと、次の一歩の候補を表示します。";
    const original = firstRecall ? firstRecall.text : recall.value;
    const originalIdea = firstRecall ? firstRecall.idea : idea.value;
    const condition = firstRecall ? firstRecall.reference : reference.value;
    const freezeLabel = firstRecall
      ? firstRecall.order !== "before_exposure"
        ? "資料が既に表示された状態で入力を固定（提示と入力の順序は未確認）"
        : firstRecall.text.trim() ? "このページの資料を開く前に入力を固定（正答・保持は未判定）" : "想起は未入力のまま固定（不正解の判定ではない）"
      : "入力中・まだ固定していない";
    frozenText.textContent = original.trim() || "初回の想起は未入力です。資料を見た後の内容は、下の補足欄に書けます。";
    frozenCondition.textContent = freezeLabel + "。" + (references[condition] || references.unknown);
    const comparisonLines = selected.filter((entry) => comparisons[entry.value])
      .map((entry) => "- " + entry.id + " / " + entry.title + "：" + comparisons[entry.value]);
    const lines = [
      "学習の歴史書との照合・継続記録", "",
      "予習ID: " + page.dataset.preparationId,
      "歴史書の版: " + page.dataset.historyVersion,
      "正本commit: " + page.dataset.sourceCommit,
      "ページ開始（UTC）: " + startedAt,
      "想起固定（UTC）: " + (firstRecall ? firstRecall.at : "未固定"),
      "最初の資料提示を観測（UTC）: " + (exposedAt || "このページでは未提示"),
      "最初に開いた欄: " + (firstDisclosure || "なし"),
      "想起の条件: " + freezeLabel,
      "他資料の参照: " + (references[condition] || references.unknown), "",
      "【最初に固定した想起：提示条件は上記】", original || "未入力", "",
      "【最初に固定した活用案：提示条件は上記】", originalIdea || "未記入", "",
      "【記録との比較（本人の判断）】", comparisonLines.length ? comparisonLines.join("\n") : "未比較", "",
      "【資料を見た後の補足・食い違い・未解決】", note.value || "未記入", "",
      "【次に行うこと：予定】", plan.value || "未定", "",
      "【実行状況：本人申告】", executionLabels[actionStatus.value] || "未確認", "",
      "【実行結果・観察したこと】", result.value || "未記入", "",
      "これはブラウザ内で作成した本人入力の引継ぎ文です。GitHub保存・能力認定・履修終了は未実施です。",
      "同じ予習IDの続きとして、当時の記録・今回の想起・補足・予定・実行結果を分けて取り込んでください。"
    ];
    handoff.value = lines.join("\n");
  }

  function freezeRecall(order = "before_exposure") {
    if (firstRecall) return;
    firstRecall = { text: recall.value, idea: idea.value, reference: reference.value, order, at: new Date().toISOString() };
    recall.readOnly = true;
    idea.readOnly = true;
    reference.disabled = true;
    freezeButton.disabled = true;
    freezeButton.textContent = "最初の入力を固定しました";
    recallStatus.textContent = firstRecall.text.trim()
      ? "ここまでの入力を固定しました。資料を見た後の追記は、歴史書の下の補足欄に残せます。"
      : "想起は未入力のまま固定しました。これからの内容は資料を見た後の補足として残せます。";
    update();
  }

  function recordExposure(disclosure, order = "before_exposure") {
    if (!exposedAt) {
      freezeRecall(order);
      exposedAt = new Date().toISOString();
      firstDisclosure = disclosure.id === "history" ? "歴史書・記録書" : "教材・振り返り";
      if (firstRecall.order !== "before_exposure") {
        recallStatus.textContent = "資料が既に開いた状態だったため、入力と提示の順序は未確認として残します。追記は補足欄へ書けます。";
      } else if (!firstRecall.text.trim()) {
        recallStatus.textContent = "想起を入力する前に資料を開きました。これからの内容は、資料を見た後の補足欄へ書けます。";
      }
    }
    update();
  }

  disclosures.forEach((disclosure) => {
    const summary = disclosure.querySelector("summary");
    if (summary) summary.addEventListener("click", () => {
      if (!disclosure.open) recordExposure(disclosure);
    });
    disclosure.addEventListener("toggle", () => {
      if (disclosure.open) recordExposure(disclosure, "already_visible");
    });
    if (disclosure.open) recordExposure(disclosure, "already_visible");
  });
  freezeButton.addEventListener("click", () => freezeRecall());
  [recall, reference, idea, note, plan, actionStatus, result].forEach((control) => {
    control.addEventListener("input", update);
    control.addEventListener("change", update);
  });
  entries.forEach((entry) => {
    const control = entry.querySelector("[data-comparison]");
    if (control) control.addEventListener("change", update);
  });
  selectButton.addEventListener("click", () => {
    update();
    handoff.focus();
    handoff.select();
    handoff.setSelectionRange(0, handoff.value.length);
    copyStatus.textContent = "記録文を選択しました。端末の「コピー」で取得し、同じ予習IDの続きとして貼り付けてください。";
  });
  page.querySelectorAll("[data-practice-only]").forEach((element) => { element.hidden = false; });
  update();
})();
