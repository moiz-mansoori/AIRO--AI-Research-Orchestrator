import asyncio
import glob
import json
import os
import threading
import time
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Form, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse

from orchestrator.graph import compile_graph
from orchestrator.state import AIROState, ComputeBudget, TaskType
from loguru import logger

# Route logs to file so Live Trace can see them
Path("logs").mkdir(exist_ok=True)
logger.add("logs/airo.log", mode="a", enqueue=True)

app = FastAPI(title="AIRO API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow Vercel frontend to communicate with Render backend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for experiment status and results
EXPERIMENTS: dict[str, dict] = {}

def run_pipeline_sync(state: AIROState):
    EXPERIMENTS[state.experiment_id] = {"status": "running", "result": None, "errors": []}
    
    try:
        graph = compile_graph()
        
        # Ensure log file exists and append empty to trigger tail
        Path("logs").mkdir(exist_ok=True)
        with open("logs/airo.log", "a") as f:
            pass
            
        final_state = graph.invoke(state, config={"recursion_limit": 50})
        
        # Ensure final_state is an AIROState object (LangGraph sometimes returns a dict)
        if isinstance(final_state, dict):
            final_state = AIROState(**final_state)
        
        EXPERIMENTS[state.experiment_id]["status"] = "complete"
        EXPERIMENTS[state.experiment_id]["result"] = {
            "experiment_id": final_state.experiment_id,
            "best_model_type": final_state.best_model_type,
            "best_run_id": final_state.best_run_id,
            "primary_metric_name": final_state.primary_metric_name(),
            "improvement_over_baseline_pct": final_state.improvement_over_baseline_pct,
            "leaderboard": [e.__dict__ for e in final_state.leaderboard],
            "critic_results": [r.__dict__ for r in final_state.critic_results],
            "agent_timings": final_state.agent_timings,
            "report_md_path": final_state.report_md_path,
            "report_pdf_path": final_state.report_pdf_path,
            "errors": final_state.errors,
        }
    except Exception as e:
        EXPERIMENTS[state.experiment_id]["status"] = "failed"
        EXPERIMENTS[state.experiment_id]["errors"] = [str(e)]


@app.post("/api/run")
async def run_experiment(
    file: UploadFile,
    task_type: str = Form(...),
    target_column: str = Form(...),
    compute_budget: str = Form(...),
    skip_curves: bool = Form(False),
    skip_shap: bool = Form(False),
):
    # Save uploaded file
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = raw_dir / file.filename
    content = await file.read()
    file_path.write_bytes(content)
    
    task_enum = TaskType.CLASSIFICATION if task_type.lower() == "classification" else TaskType.REGRESSION
    budget_enum = ComputeBudget(compute_budget.lower())
    
    state = AIROState(
        dataset_path=str(file_path),
        task_type=task_enum,
        target_column=target_column,
        compute_budget=budget_enum,
    )
    
    # Run in background thread
    thread = threading.Thread(target=run_pipeline_sync, args=(state,))
    thread.start()
    
    return {"experiment_id": state.experiment_id}


@app.get("/api/status/{experiment_id}")
async def get_status(experiment_id: str):
    return EXPERIMENTS.get(experiment_id, {"status": "not_found"})


async def log_generator(experiment_id: str):
    log_file = Path("logs/airo.log")
    if not log_file.exists():
        log_file.write_text("")
        
    with open(log_file, "r", encoding="utf-8") as f:
        # Start from beginning so user sees full progress
        f.seek(0)
        
        while True:
            line = f.readline()
            if line:
                yield f"data: {line.strip()}\n\n"
            else:
                status = EXPERIMENTS.get(experiment_id, {}).get("status", "running")
                if status in ("complete", "failed"):
                    break
                await asyncio.sleep(0.5)

@app.get("/api/logs/{experiment_id}")
async def stream_logs(experiment_id: str):
    return StreamingResponse(log_generator(experiment_id), media_type="text/event-stream")


@app.get("/api/experiments")
async def list_experiments():
    import pandas as pd
    report_dirs = sorted(glob.glob("reports/*/leaderboard.csv"), reverse=True)
    experiments = []
    
    for csv_path in report_dirs[:10]:
        exp_id = Path(csv_path).parent.name
        try:
            df = pd.read_csv(csv_path)
            if not df.empty:
                top = df.iloc[0]
                experiments.append({
                    "experiment_id": exp_id,
                    "best_model_type": str(top.get("model_type", "—")),
                    "best_metric": float(top.get("primary_metric", 0)),
                    "verdict": str(top.get("verdict", "—")),
                    "has_report": (Path(csv_path).parent / "airo_report.md").exists()
                })
        except Exception:
            pass
    return experiments


@app.get("/api/report/{experiment_id}/pdf")
async def get_report_pdf(experiment_id: str):
    pdf_path = Path(f"reports/{experiment_id}/airo_report.pdf")
    if pdf_path.exists():
        return FileResponse(pdf_path, filename=f"airo_report_{experiment_id}.pdf")
    return {"error": "Not found"}


@app.get("/api/report/{experiment_id}/markdown")
async def get_report_markdown(experiment_id: str):
    md_path = Path(f"reports/{experiment_id}/airo_report.md")
    if md_path.exists():
        return PlainTextResponse(md_path.read_text(encoding="utf-8"))
    return {"error": "Not found"}
