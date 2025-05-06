// script.js (Updated to stream /generate_notes and /generate_paper and fetch markscheme afterward)
document.addEventListener("DOMContentLoaded", () => {
  const BASE_URL = window.location.hostname === "localhost"
    ? "http://127.0.0.1:5000"
    : "https://igcse-toolkit.onrender.com";

  const tabs = {
    home: document.getElementById("tab-home"),
    notes: document.getElementById("tab-notes"),
    paper: document.getElementById("tab-paper"),
  };

  const tabContents = {
    home: document.getElementById("home-tab"),
    notes: document.getElementById("notes-tab"),
    paper: document.getElementById("paper-tab"),
  };

  const boardDropdown = document.getElementById("exam-board");
  const subjectDropdown = document.getElementById("subject");
  const topicDropdown = document.getElementById("topic");
  const subtopicDropdown = document.getElementById("subtopic");
  const learnerDropdown = document.getElementById("learner-type");
  const generateBtn = document.getElementById("generate-btn");
  const outputDiv = document.getElementById("notes-output");
  const flowchartContainer = document.getElementById("flowchart-container");
  const chatContainer = document.getElementById("chatbot-container");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");

  const paperBoardDropdown = document.getElementById("paper-board");
  const paperSubjectDropdown = document.getElementById("paper-subject");
  const paperTopicDropdown = document.getElementById("paper-topic");
  const paperSubtopicDropdown = document.getElementById("paper-subtopic");
  const paperOutput = document.getElementById("paper-output");
  const markschemeOutput = document.getElementById("markscheme-output");
  const generatePaperBtn = document.getElementById("generate-paper-btn");

  let currentNotes = "";
  let currentPaperText = "";

  function showTab(name) {
    Object.keys(tabs).forEach(key => {
      tabs[key].classList.remove("active");
      tabContents[key].style.display = "none";
    });
    tabs[name].classList.add("active");
    tabContents[name].style.display = "block";
    chatContainer.style.display = name === "notes" ? "block" : "none";
  }

  function resetDropdown(dropdown, defaultText) {
    dropdown.innerHTML = `<option value="">-- ${defaultText} --</option>`;
  }

  function updateGenerateButtonState() {
    const board = boardDropdown.value;
    const subject = subjectDropdown.value;
    const topic = topicDropdown.value;
    const subtopic = subtopicDropdown.value;
    const learnerType = learnerDropdown.value;
    generateBtn.disabled = !(board && subject && topic && subtopic && learnerType);
  }

  function updateGeneratePaperButtonState() {
    const board = paperBoardDropdown.value;
    const subject = paperSubjectDropdown.value;
    const topic = paperTopicDropdown.value;
    const subtopic = paperSubtopicDropdown.value;
    generatePaperBtn.disabled = !(board && subject && topic && subtopic);
  }

  showTab("home");
  tabs.home.addEventListener("click", () => showTab("home"));
  tabs.notes.addEventListener("click", () => showTab("notes"));
  tabs.paper.addEventListener("click", () => showTab("paper"));

  boardDropdown.addEventListener("change", () => {
    resetDropdown(subjectDropdown, "Select Subject");
    resetDropdown(topicDropdown, "Select Topic");
    resetDropdown(subtopicDropdown, "Select Subtopic");
    outputDiv.innerHTML = "";
    updateGenerateButtonState();

    const board = boardDropdown.value;
    if (!board) return;

    fetch(`${BASE_URL}/get_subjects/${board}`)
      .then(res => res.json())
      .then(data => {
        data.subjects?.forEach(subject => {
          const option = document.createElement("option");
          option.value = subject;
          option.textContent = subject;
          subjectDropdown.appendChild(option);
        });
      });
  });

  subjectDropdown.addEventListener("change", () => {
    resetDropdown(topicDropdown, "Select Topic");
    resetDropdown(subtopicDropdown, "Select Subtopic");
    outputDiv.innerHTML = "";
    updateGenerateButtonState();

    const board = boardDropdown.value;
    const subject = subjectDropdown.value;
    if (!board || !subject) return;

    fetch(`${BASE_URL}/get_topics/${board}/${subject}`)
      .then(res => res.json())
      .then(data => {
        data.topics?.forEach(topic => {
          const option = document.createElement("option");
          option.value = topic;
          option.textContent = topic;
          topicDropdown.appendChild(option);
        });
      });
  });

  topicDropdown.addEventListener("change", () => {
    resetDropdown(subtopicDropdown, "Select Subtopic");
    outputDiv.innerHTML = "";
    updateGenerateButtonState();

    const board = boardDropdown.value;
    const subject = subjectDropdown.value;
    const topic = topicDropdown.value;
    if (!board || !subject || !topic) return;

    fetch(`${BASE_URL}/get_subtopics`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ board, subject, topic })
    })
    .then(res => res.json())
    .then(data => {
      const fullOption = document.createElement("option");
      fullOption.value = "full";
      fullOption.textContent = "🌐 Full Topic";
      subtopicDropdown.appendChild(fullOption);
      data.subtopics?.forEach(sub => {
        const option = document.createElement("option");
        option.value = sub;
        option.textContent = sub;
        subtopicDropdown.appendChild(option);
      });
    });
  });

  learnerDropdown.addEventListener("change", updateGenerateButtonState);
  subtopicDropdown.addEventListener("change", updateGenerateButtonState);

  generateBtn.addEventListener("click", (e) => {
    e.preventDefault();
    const board = boardDropdown.value;
    const subject = subjectDropdown.value;
    const topic = topicDropdown.value;
    const subtopic = subtopicDropdown.value;
    const learnerType = learnerDropdown.value;

    outputDiv.innerHTML = "<p><em>Generating notes... please wait.</em></p>";
    flowchartContainer.innerHTML = "";
    chatContainer.style.display = "none";
    currentNotes = "";

    fetch(`${BASE_URL}/generate_notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ board, subject, topic, subtopic, learner_type: learnerType })
    }).then(response => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let result = "";

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            currentNotes = result;
            chatContainer.style.display = "block";
            if (learnerType === "visual") {
              const mermaidElement = document.createElement("div");
              mermaidElement.classList.add("mermaid");
              mermaidElement.textContent = `flowchart TD\n${currentNotes}`;
              flowchartContainer.innerHTML = "";
              flowchartContainer.appendChild(mermaidElement);
              try { window.mermaid.run(); } catch (err) {
                console.error("Mermaid render failed:", err);
              }
            } else {
              flowchartContainer.innerHTML = "";
              outputDiv.innerHTML = marked.parse(currentNotes);
            }
            return;
          }
          result += decoder.decode(value, { stream: true });
          read();
        });
      }
      read();
    }).catch(err => {
      outputDiv.innerHTML = `<p class='text-danger'>${err.message || "Error."}</p>`;
    });
  });

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;

    outputDiv.innerHTML = "<p><em>Updating notes... please wait.</em></p>";

    fetch(`${BASE_URL}/chat_refine_notes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ original_notes: currentNotes, message })
    })
    .then(res => res.json())
    .then(data => {
      currentNotes = data.refined_notes;
      outputDiv.innerHTML = marked.parse(currentNotes);
    })
    .catch(err => {
      outputDiv.innerHTML = `<p class='text-danger'>Failed to refine notes.</p>`;
    });

    chatInput.value = "";
  });

  [paperBoardDropdown, paperSubjectDropdown, paperTopicDropdown, paperSubtopicDropdown].forEach(el => {
    el.addEventListener("change", updateGeneratePaperButtonState);
  });

  paperBoardDropdown.addEventListener("change", () => {
    resetDropdown(paperSubjectDropdown, "Select Subject");
    resetDropdown(paperTopicDropdown, "Select Topic");
    resetDropdown(paperSubtopicDropdown, "Select Subtopic");

    const board = paperBoardDropdown.value;
    if (!board) return;

    fetch(`${BASE_URL}/get_subjects/${board}`)
      .then(res => res.json())
      .then(data => {
        data.subjects?.forEach(subject => {
          const option = document.createElement("option");
          option.value = subject;
          option.textContent = subject;
          paperSubjectDropdown.appendChild(option);
        });
      });
  });

  paperSubjectDropdown.addEventListener("change", () => {
    resetDropdown(paperTopicDropdown, "Select Topic");
    resetDropdown(paperSubtopicDropdown, "Select Subtopic");

    const board = paperBoardDropdown.value;
    const subject = paperSubjectDropdown.value;
    if (!board || !subject) return;

    fetch(`${BASE_URL}/get_topics`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ board, subject })
    })
    .then(res => res.json())
    .then(data => {
      data.topics?.forEach(topic => {
        const option = document.createElement("option");
        option.value = topic;
        option.textContent = topic;
        paperTopicDropdown.appendChild(option);
      });
    });
  });

  paperTopicDropdown.addEventListener("change", () => {
    resetDropdown(paperSubtopicDropdown, "Select Subtopic");

    const board = paperBoardDropdown.value;
    const subject = paperSubjectDropdown.value;
    const topic = paperTopicDropdown.value;
    if (!board || !subject || !topic || topic === "all") return;

    fetch(`${BASE_URL}/get_subtopics`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ board, subject, topic })
    })
    .then(res => res.json())
    .then(data => {
      const fullOption = document.createElement("option");
      fullOption.value = "full";
      fullOption.textContent = "🌐 Full Topic";
      paperSubtopicDropdown.appendChild(fullOption);
      data.subtopics?.forEach(sub => {
        const option = document.createElement("option");
        option.value = sub;
        option.textContent = sub;
        paperSubtopicDropdown.appendChild(option);
      });
    });
  });

  generatePaperBtn.addEventListener("click", (e) => {
    e.preventDefault();
    const board = paperBoardDropdown.value;
    const subject = paperSubjectDropdown.value;
    const topic = paperTopicDropdown.value;
    const subtopic = paperSubtopicDropdown.value;

    paperOutput.innerHTML = "<p><em>Generating paper... please wait.</em></p>";
    markschemeOutput.innerHTML = "";
    let result = "";

    fetch(`${BASE_URL}/generate_paper`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ board, subject, topic, subtopic })
    })
    .then(response => {
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      function read() {
        reader.read().then(({ done, value }) => {
          if (done) {
            currentPaperText = result;
            paperOutput.innerHTML = `<h4>Paper</h4><pre>${currentPaperText}</pre>`;
            fetch(`${BASE_URL}/generate_markscheme`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ paper_text: currentPaperText })
            })
            .then(async res => {
              if (!res.ok || !res.body) {
                throw new Error("Failed to stream mark scheme.");
              }
            
              const reader = res.body.getReader();
              const decoder = new TextDecoder("utf-8");
              let result = "";
            
              while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                result += decoder.decode(value, { stream: true });
              }
            
              markschemeOutput.innerHTML = `<h4>Mark Scheme</h4><pre>${result}</pre>`;
            })
            .catch(err => {
              markschemeOutput.innerHTML = `<p class='text-danger'>Failed to fetch mark scheme: ${err.message}</p>`;
            });            
            return;
          }
          result += decoder.decode(value, { stream: true });
          read();
        });
      }
      read();
    })
    .catch(err => {
      paperOutput.innerHTML = `<p class='text-danger'>${err.message || "Error."}</p>`;
    });
  });
});
