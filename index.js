import Fastify from "fastify";
import fastifyWs from "@fastify/websocket";
import fastifyFormbody from "@fastify/formbody";
import dotenv from "dotenv";
dotenv.config();

const PORT = process.env.PORT || 8080;
const PYTHON_HOOK_URL = "http://127.0.0.1:5001/stream"; // where Python is listening

function forwardToPython(payload) {
  // fire-and-forget so streaming isn’t blocked
  axios.post(PYTHON_HOOK_URL, payload).catch(() => {});
}

let DOMAIN = process.env.NGROK_URL || "";
if (DOMAIN.startsWith("http")) {
  DOMAIN = new URL(DOMAIN).host; // strips https:// and path if someone pasted it
}


const WS_URL = `wss://${DOMAIN}/ws`;
const WELCOME_GREETING =
  "Hi! I am Adulter an AI assistant. How can I plan your day?";
const SYSTEM_PROMPT = `
You are a helpful, voice-first assistant. Your replies are spoken to the caller, so be clear and concise. Spell out all numbers in words (for example, “twenty” not “20”). Do not use emojis, bullet points, asterisks, or special symbols. Keep responses to one or two short sentences per turn.

Primary task: schedule events on the caller’s Google Calendar. Collect the necessary details with brief follow-up questions if any are missing.

Required event fields to gather:
• Title or purpose of the event.
• Date and time with timezone. Convert relative phrases like “tomorrow at three” or “next Friday afternoon” into absolute ISO datetimes.
• Location (address, phone, or meeting link).

Flow:
1) If the user expresses scheduling intent, gather any missing details with a short clarifying question.
2) When enough details are given, confirm once in a natural sentence. Example: “Great, I will set up a coffee chat on Tuesday, June fourth at three p m Pacific at Blue Bottle.” 
3) After confirmation, say something like “Setting it up on Google Calendar now,” and then call the calendar tool.
4) On success, acknowledge briefly: “All set. Your event has been added.”

Other guidance:
• Only call the tool after confirmation. 
• Keep your tone friendly but concise.
• If asked for a programming joke, use the get_programming_joke tool. For other jokes, answer from your own knowledge.
• Do not reveal tool names or schemas to the caller. Do not narrate your reasoning. Speak naturally and keep it short.`;
const sessions = new Map();

import OpenAI from "openai";
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

import axios from "axios";
const tools = [
  {
    type: "function",
    function: {
      name: "get_programming_joke",
      description: "Fetches a programming joke",
      parameters: {
        type: "object",
        properties: {},
        required: [],
        additionalProperties: false,
      },
      strict: true,
    },
  },
];

async function getJoke() {
  // Use jokeapi.dev to fetch a clean joke
  const response = await axios.get(
    "https://v2.jokeapi.dev/joke/Programming?safe-mode"
  );
  const data = response.data;
  return data.type === "single"
    ? data.joke
    : `${data.setup} ... ${data.delivery}`;
}

const toolFunctions = {
  get_programming_joke: async () => getJoke(),
};

async function aiResponseStream(messages, ws) {
  const stream = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: messages,
    stream: true,
    tools: tools,
  });

  const assistantSegments = [];
  console.log("Received response chunks:");
  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content || "";
    const toolCalls = chunk.choices[0].delta.tool_calls || [];

    for (const toolCall of toolCalls) {
      const toolName = toolCall.function.name;
      const toolFn = toolFunctions[toolName];

      if (toolFn) {
        const toolResponse = await toolFn();

        // Append tool call request and the result with the "tool" role
        messages.push({
          role: "assistant",
          tool_calls: [
            {
              id: toolCall.id,
              function: {
                name: toolName,
                arguments: "{}",
              },
              type: "function",
            },
          ],
        });

        messages.push({
          role: "tool",
          tool_call_id: toolCall.id,
          content: toolResponse,
        });

        // Send the completed tool response to the client
        ws.send(
          JSON.stringify({ type: "text", token: toolResponse, last: true })
        );
        // forward to Python
        forwardToPython({ token: toolResponse, last: true });
        
        assistantSegments.push(toolResponse);
        console.log(`Fetched ${toolName}:`, toolResponse);
      }
    }

    // Send each token
    console.log(content);
    ws.send(
      JSON.stringify({
        type: "text",
        token: content,
        last: false,
      })
    );

    forwardToPython({ token: content, last: false });
    assistantSegments.push(content);
  }

  const finalResponse = assistantSegments.join("");
  console.log("Assistant response complete:", finalResponse);
  messages.push({
    role: "assistant",
    content: finalResponse,
  });
}

function handleInterrupt(callSid, utteranceUntilInterrupt) {
  const conversation = sessions.get(callSid);

  let updatedConversation = [...conversation];

  const interruptedIndex = updatedConversation.findIndex(
    (message) =>
      message.role === "assistant" &&
      message.content.includes(utteranceUntilInterrupt)
  );

  if (interruptedIndex !== -1) {
    const interruptedMessage = updatedConversation[interruptedIndex];

    const interruptPosition = interruptedMessage.content.indexOf(
      utteranceUntilInterrupt
    );
    const truncatedContent = interruptedMessage.content.substring(
      0,
      interruptPosition + utteranceUntilInterrupt.length
    );

    updatedConversation[interruptedIndex] = {
      ...interruptedMessage,
      content: truncatedContent,
    };

    updatedConversation = updatedConversation.filter(
      (message, index) =>
        !(index > interruptedIndex && message.role === "assistant")
    );
  }

  sessions.set(callSid, updatedConversation);
}

const fastify = Fastify({ logger: true });
fastify.register(fastifyWs);
fastify.register(fastifyFormbody);
fastify.all("/twiml", async (request, reply) => {
  reply.type("text/xml").send(
    `<?xml version="1.0" encoding="UTF-8"?>
    <Response>
      <Connect>
        <ConversationRelay url="${WS_URL}" welcomeGreeting="${WELCOME_GREETING}" />
      </Connect>
    </Response>`
  );
});

fastify.register(async function (fastify) {
  fastify.get("/ws", { websocket: true }, (ws, req) => {
    ws.on("message", async (data) => {
      const message = JSON.parse(data);

      switch (message.type) {
        case "setup":
          const callSid = message.callSid;
          console.log("Setup for call:", callSid);
          ws.callSid = callSid;
          sessions.set(callSid, [{ role: "system", content: SYSTEM_PROMPT }]);
          break;
        case "prompt":
          console.log("Processing prompt:", message.voicePrompt);

          const messages = sessions.get(ws.callSid);
          messages.push({ role: "user", content: message.voicePrompt });

          await aiResponseStream(messages, ws);

          // Send the final "last" token when streaming completes
          ws.send(
            JSON.stringify({
              type: "text",
              token: "",
              last: true,
            })
          );
          break;
        case "interrupt":
          console.log(
            "Handling interruption; last utterance: ",
            message.utteranceUntilInterrupt
          );
          handleInterrupt(ws.callSid, message.utteranceUntilInterrupt);
          break;
        default:
          console.warn("Unknown message type received:", message.type);
          break;
      }
    });

    ws.on("close", () => {
      console.log("WebSocket connection closed");
      sessions.delete(ws.callSid);
    });
  });
});

try {
  fastify.listen({ port: PORT });
} catch (err) {
  fastify.log.error(err);
  process.exit(1);
}
