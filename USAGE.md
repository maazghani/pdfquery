### 📝 **`pdfquery` CLI – complete usage guide**

The CLI has **two sub-commands**—`index` and `query`.  
Run `pdfquery --help`, `pdfquery index --help`, or `pdfquery query --help` any time for built-in help.

---

## 1. `index` — build / update a FAISS index

| Option | Required | Description |
|--------|----------|-------------|
| `--source <PATH>` | **yes** | Path to the PDF file you want to index. |
| `--name <SLUG>`   | **yes** | A short slug used as the on-disk folder name (e.g. `cloud-sec`, `wafr`). |
| `--key <OPENAI_API_KEY>` | no | OpenAI key just for this command. (If omitted the CLI uses `$OPENAI_API_KEY` from your environment.) |

**Example**

```bash
pdfquery index \
  --source docs/aws_well_architected_framework.pdf \
  --name wafr \
  --key $OPENAI_API_KEY
```

Creates a folder `vector/wafr/` containing `faiss.index` and `metadata.jsonl`.

---

## 2. `query` — run a natural-language question against indexed PDF content

| Option | Required | Description |
|--------|----------|-------------|
| `--name <SLUG>`     | **yes** | Index slug to load (from the `vector/` folder). |
| `<question>`        | **yes** | Your query in natural language. |
| `--model <MODEL>`   | no | OpenAI chat model to use (default: `gpt-4o-mini`). |
| `--top-k <INT>`     | no | Number of relevant chunks to retrieve for context (default: `5`). |
| `--key <OPENAI_API_KEY>` | no | OpenAI key to use (overrides environment). |
| `--dry-run`         | no | Print retrieved chunks only — don’t call OpenAI API. |

**Example**

```bash
pdfquery query \
  --name wafr \
  "What are the core security practices recommended by AWS?"
```

Use `--dry-run` to inspect which chunks will be sent to GPT:

```bash
pdfquery query --dry-run --name wafr "What is the AWS shared responsibility model?"
```
