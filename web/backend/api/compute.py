import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "framework" / "src"))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from calc_framework.config.manager import AdapterManager

router = APIRouter(prefix="/api/compute", tags=["compute"])

ADAPTER_ROOT = Path(__file__).resolve().parents[3] / "framework" / "adapters"
_manager = AdapterManager(ADAPTER_ROOT)


class EvaluateRequest(BaseModel):
    adapter: str
    context: dict


class EvaluateResponse(BaseModel):
    outputs: dict[str, float]
    node_values: dict[str, float | str | None]
    execution_order: list[str]


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(req: EvaluateRequest):
    try:
        pkg = _manager.load(req.adapter)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        result = pkg.dag_service.evaluate(req.context)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return EvaluateResponse(
        outputs=result.outputs,
        node_values={k: v for k, v in result.node_values.items()},
        execution_order=result.execution_order,
    )
