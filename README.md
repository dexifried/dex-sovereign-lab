# ModernBERT Intent Router Lab

A small Gradio-based experiment for fine-tuning `answerdotai/ModernBERT-base` as a text intent classifier.

> **Status:** Research prototype. This repository demonstrates a local training interface, not a production-ready classifier or a validated benchmark result.

## What it does

The application:

- loads labelled examples from `intent_dataset.csv`;
- discovers the available intent labels dynamically;
- tokenizes text with the ModernBERT tokenizer;
- fine-tunes a sequence-classification head;
- saves the trained model and tokenizer locally;
- exposes the training action through a minimal Gradio interface.

## Current architecture

```text
intent_dataset.csv
        │
        ▼
Dataset validation and label mapping
        │
        ▼
ModernBERT tokenization
        │
        ▼
Sequence-classification fine-tuning
        │
        ▼
dex_router_model/
```

## Dataset format

The CSV is expected to contain two columns:

```csv
text,label
"show nearby stops",nearby_stop
"when is the next bus",next_departure
```

Use only data you have permission to publish. Do not commit private conversations, credentials, personal records, or production logs.

## Run locally

Create a Python environment, install the project dependencies, provide `intent_dataset.csv`, and run:

```bash
python app.py
```

GPU acceleration is optional, but the current configuration enables FP16 training and therefore assumes compatible hardware.

## Important limitations

The current prototype does **not** yet provide:

- a train/validation/test split;
- accuracy, macro-F1, or confusion-matrix reporting;
- reproducible seed configuration;
- class-imbalance handling;
- hyperparameter comparison;
- automated tests;
- production inference or deployment tooling.

Until those are added, successful completion of a training run should not be treated as evidence that the resulting model generalizes well.

## Planned improvements

- Add deterministic dataset splitting and seed control.
- Report accuracy, macro-F1, per-class metrics, and a confusion matrix.
- Compare ModernBERT against a simple baseline.
- Validate required CSV columns and reject malformed rows.
- Add a small synthetic example dataset.
- Add tests and a reproducible dependency lockfile.
- Separate training, evaluation, and inference commands.

## Attribution

Project direction, experiment design, testing decisions, and acceptance criteria are by Austin Harvey. Implementation has been substantially AI-assisted and should be evaluated by the behaviour and evidence in the repository rather than by an assumption that every line was written manually.

## Licence

This project is available under the [MIT License](LICENSE).
