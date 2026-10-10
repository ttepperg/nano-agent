let isRunning = false;

function scrollToBottom() {
    const conversation = document.getElementById("conversation");

    conversation.scrollTo({
        top: conversation.scrollHeight,
        behavior: "smooth"
    });
}
function addMessage(role, text) {
    const message = document.createElement("div");
    message.className = `message ${role}`;

    const label = document.createElement("strong");
    label.className = "message-label";
    label.textContent = role === "user" ? "You" : "Nano Agent";

    const content = document.createElement("div");
    content.textContent = text;

    message.append(label, content);
    document.getElementById("conversation").appendChild(message);

    scrollToBottom();

    return content;
}

async function runAgent() {
    const taskInput = document.getElementById("task");
    const task = taskInput.value.trim();

    if (!task || isRunning) return;

    isRunning = true;
    const runButton = document.querySelector("#composer button");
    runButton.disabled = true;

    addMessage("user", task);
    const agentContent = addMessage("agent", "Thinking...");
    taskInput.value = "";

    try {
        const response = await fetch("/run", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({task: task})
        });

        if (!response.ok) {
            const errorText = await response.text();
            agentContent.textContent =
                `Server error (${response.status}): ` +
                (errorText || "The request failed.");
            return;
        }

        const data = await response.json();
        agentContent.textContent = data.response;

        if (data.usage) {
            document.getElementById("prompt-tokens").textContent =
                `Prompt: ${data.usage.prompt_tokens}`;
            document.getElementById("completion-tokens").textContent =
                `Completion: ${data.usage.completion_tokens}`;
            document.getElementById("total-tokens").textContent =
                `Total: ${data.usage.total_tokens}`;
        }

    } catch (error) {
        agentContent.textContent =
            "Could not connect to the server.";
    } finally {
        isRunning = false;
        runButton.disabled = false;
        scrollToBottom();
    }
}

document.getElementById("task")
.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        event.preventDefault();
        runAgent();
    }
});
