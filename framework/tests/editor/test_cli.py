from __future__ import annotations

import json

from calc_framework.dag.schema import (
    DAGGraph,
    DAGOutput,
    DAGVariable,
    ExprNode,
)
from calc_framework.dag.serializer import dag_to_dict
from calc_framework.editor.__main__ import main
from calc_framework.ui.layout import load_layout

SIMPLE_DAG = DAGGraph(
    name="simple",
    variables={
        "a": DAGVariable(type="float", source="character"),
        "b": DAGVariable(type="float", source="computed"),
    },
    nodes={"r": ExprNode(expr="a + b")},
    outputs={"result": DAGOutput(node="r", label="result")},
)


class TestCLI:
    def test_auto(self, tmp_path):
        dag_path = tmp_path / "dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SIMPLE_DAG)), encoding="utf-8")
        out_path = tmp_path / "layout.json"

        rc = main(["--dag", str(dag_path), "--auto", "-o", str(out_path)])
        assert rc == 0
        assert out_path.exists()

        with out_path.open(encoding="utf-8") as f:
            layout = load_layout(json.load(f))
        assert layout.name == "Computed Layout"
        assert len(layout.sections) >= 1
        output_sec = layout.find_section("outputs")
        assert output_sec is not None
        assert "result" in output_sec.outputs

    def test_auto_with_custom_name(self, tmp_path):
        dag_path = tmp_path / "dag.json"
        dag_path.write_text(json.dumps(dag_to_dict(SIMPLE_DAG)), encoding="utf-8")
        out_path = tmp_path / "layout.json"

        rc = main(["--dag", str(dag_path), "--auto", "-o", str(out_path), "--name", "MyLayout"])
        assert rc == 0

        with out_path.open(encoding="utf-8") as f:
            layout = load_layout(json.load(f))
        assert layout.name == "MyLayout"

    def test_missing_dag(self, capsys):
        rc = main(["--dag", "/nonexistent/dag.json", "--auto"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "不存在" in captured.err

    def test_invalid_dag(self, tmp_path, capsys):
        bad = tmp_path / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        rc = main(["--dag", str(bad), "--auto"])
        assert rc == 1
