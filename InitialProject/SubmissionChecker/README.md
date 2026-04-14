# Initial Project 2026 Submission Checker

## Contents

- `check_submission.py`: command-line checker for one student submission folder
- `src/checker/solution_checker.py`: validation logic
- `config/file_formats.yaml`: allowed variable names, variable limits, expected row counts
- `requirements.txt`: minimal Python dependency for the checker

## Quick start

From this `SubmissionChecker/` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python check_submission.py ../DummySubmission/solutions_DummyTA_Assistant
```

## Expected submission structure (per student)

A single student folder should include:

- One `Description_*.txt`
- For each task type (`Classification`, `Regression`, `Clustering`):
  - one prediction file: `Type_FirstLast_SolutionName.csv`
  - one variable list: `Type_FirstLast_SolutionName_VariableList.csv`

Prediction files are checked for:

- `index,value` format per line
- correct number of rows (60k/40k/5950)
- valid ranges/types