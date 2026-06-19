import Anthropic from "@anthropic-ai/sdk";
import express, { Request, Response } from "express";

const app = express();
app.use(express.json());

const client = new Anthropic();

app.post("/summarize", async (req: Request, res: Response) => {
  const { text } = req.body as { text?: string };

  if (!text || typeof text !== "string" || text.trim() === "") {
    res.status(400).json({ error: "Campo 'text' é obrigatório." });
    return;
  }

  try {
    const stream = client.messages.stream({
      model: "claude-opus-4-8",
      max_tokens: 16000,
      messages: [
        {
          role: "user",
          content: `Resuma o seguinte texto de forma clara e concisa, mantendo os pontos mais importantes:\n\n${text}`,
        },
      ],
    });

    const message = await stream.finalMessage();

    const summary = message.content
      .filter((block): block is Anthropic.TextBlock => block.type === "text")
      .map((block) => block.text)
      .join("");

    res.json({
      summary,
      input_tokens: message.usage.input_tokens,
      output_tokens: message.usage.output_tokens,
    });
  } catch (err) {
    const error = err as Error;
    res.status(500).json({ error: error.message });
  }
});

app.get("/health", (_req: Request, res: Response) => {
  res.json({ status: "ok" });
});

const PORT = process.env.PORT ?? 3000;
app.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});
