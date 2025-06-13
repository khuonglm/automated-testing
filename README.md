# Project Environment Setup and Usage Guide

This project consists of multiple components with different Python version requirements and dependencies. Follow the instructions below to set up your environment and run the various parts of the project.

---

## 🔧 Environment Setup

### Step 1: Dependency Extraction

- **Python Version**: 3.10  
  > *Note: While not explicitly tested, Python 3.9 is expected to be compatible.*

- **Dependencies**: Install using the `requirements.txt` file located in the root directory:
  ```bash
  pip install -r requirements.txt
  ```

### Step 2: Remaining Components (RealWorld Compatibility)

- **Python Version**: 3.9  
  > This version is required to ensure compatibility with the [RealWorld](https://github.com/gothinkster/realworld) repository.

- **Dependencies**: Install using the `backend/requirements` file:
  ```bash
  pip install -r backend/requirements/dev.txt
  ```

---

## 🚀 Usage

### 1. Preprocessing

To run preprocessing, navigate to the `preprocessing` folder and use the environment file specified in the `preprocessing/README.md`:
```bash
  cd preprocessing
  python preprocessing.py
```

### 2. Fuzzing and Statistics

To run the fuzzing process and collect statistics:
```bash
  cd fuzzing
  python fuzzer.py
```
