# START HERE — Sk Mursalim

## 1. Open this folder in IBM Bob IDE

Do not start by asking Bob to rebuild the whole project. The repository already has a working baseline.

## 2. Confirm Bob account

Use the hackathon-provisioned Bob account from the event invite, not a personal account.

## 3. Start with Plan mode

Paste the Task 01 prompt from `docs/bob-workflow.md`. Review the plan before allowing edits.

## 4. Then use focused Agent tasks

Run Task 02 → Task 03 → Task 04 → Task 05 → Task 06 from `docs/bob-workflow.md` as separate tasks. Keep each task narrow so the Bob history clearly demonstrates what Bob did.

## 5. Capture evidence immediately

After every Bob task that contributes to the submission:

- open the task in Bob;
- open its session-consumption summary;
- capture the required PNG screenshot;
- export the task history if the event guide requires it;
- save both under `bob_sessions/` using a clear task number/name.

Do not fabricate any of these files.

## 6. Prove the product works

Run:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -e .
reviewsentinel scan sample_repo --out reports/sample --no-explain
reviewsentinel-web
```

Open `http://localhost:8000` and click **Scan demo repo**.

## 7. Before submission

Follow `docs/submission-checklist.md` and `docs/hackathon-compliance.md`. The online deployment, Bob evidence, video, deck, and actual impact measurements must be supplied by you during the event.
