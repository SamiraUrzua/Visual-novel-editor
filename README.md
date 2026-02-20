# Visual Novel Editor

A desktop GUI editor for writing visual novel scripts in YAML format.
It's made for my own visual novel engine.

Built with Python and PySide6.

## Features

- Create and manage sequences with metadata (title, background, characters)
- Add commands: dialogue, emotions, animations, backgrounds, music, sound, choices
- Nested choice/option trees with their own sequences
- Import and export YAML files
- Character list with mention insertion for dialogue
- Dark theme UI

## Requirements

```bash
pip install PySide6 pyyaml
```

## Usage

```bash
python main.py
```

## YAML Format

```yaml
sequences:
  intro:
    title: Introduction
    background: bedroom
    characters:
      luna: center
    sequence:
      - char: luna
      - emotion: happy
      - say: "Hello!"
      - choice:
        - option: "Hi!"
          sequence:
            - say: "Nice to meet you"
        - option: "Hey"
          sequence:
            - say: "Hey yourself"
```
