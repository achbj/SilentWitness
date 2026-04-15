# SilentWitness

> On-device AI that documents abuse without internet, protecting survivors' privacy

## Overview

SilentWitness is an offline-first AI application that helps abuse survivors safely document evidence without requiring internet connectivity. Built with Gemma 4 for the Kaggle Gemma 4 Good Hackathon (Safety & Trust track).

## Features

- **Voice Documentation**: Record evidence through voice, processed locally
- **Evidence Classification**: AI-powered categorization of abuse type, severity, evidence strength
- **Offline-First**: Works without internet - critical for survivors in unsafe situations
- **Encrypted Storage**: AES-256 encrypted local storage, tamper-proof
- **Decoy Mode**: Disguised as calculator/notes app for safety
- **Legal Export**: Generate court-admissible documentation format

## Technical Stack

| Component | Technology |
|-----------|------------|
| AI Engine | Gemma 4 E2B (quantized) |
| Runtime | Ollama / llama.cpp |
| ML Classifier | PyTorch + ONNX |
| Storage | SQLite + SQLCipher |
| Platform | React Native + Expo |

## Architecture

```
Voice Input → Gemma 4 (Local) → Evidence Classifier → Encrypted Storage → Legal Export
```

## Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/SilentWitness.git

# Install dependencies
pip install -r requirements.txt

# Pull Gemma model
ollama pull gemma3:1b  # or gemma4:e2b when available

# Run locally
python src/main.py
```

## Development Status

- [x] Project structure initialized
- [ ] Gemma 4 setup
- [ ] Voice processing pipeline
- [ ] Evidence classifier
- [ ] Encrypted storage
- [ ] Mobile app UI
- [ ] Demo video

## License

MIT License - Open source for transparency and trust

## Impact

- **Global**: 1 in 3 women experience domestic violence (WHO)
- **US**: 10 million abuse incidents annually
- **Documentation gap**: 70% of survivors lack documented evidence
- **Tech gap**: No offline-first abuse documentation tool exists

---

Built with Gemma 4 for the [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon)