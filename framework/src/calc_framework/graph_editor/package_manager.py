# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""包管理器 — 加载 JSON/ZIP 包，注册复合节点类型。"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from calc_framework.logging import get_logger

from .schema import (
    GraphDocument,
)
from .serializer import document_from_json

logger = get_logger(__name__)

# 默认子图包目录
# __file__ = framework/src/calc_framework/graph_editor/package_manager.py
# parents[0] = graph_editor/
# parents[1] = calc_framework/
# parents[2] = src/
# parents[3] = framework/
_DEFAULT_PACKAGES_DIR = Path(__file__).resolve().parents[3] / "packages"


@dataclass
class CompositePortDef:
    """复合节点的一个端口定义。"""

    label: str

    node_id: str

    port_index: int


@dataclass
class CompositeTypeDef:
    """复合节点类型的注册信息。"""

    type_id: str  # "@packagename/graphname"

    display_name: str  # 显示名称

    package_name: str  # 包名（ZIP 文件名）

    source_file: str  # 原始文件名

    in_ports: list[CompositePortDef] = field(default_factory=list)

    out_ports: list[CompositePortDef] = field(default_factory=list)

    source_graph_json: str = ""

    @property
    def in_count(self) -> int:
        """in_count。"""
        return len(self.in_ports)

    @property
    def out_count(self) -> int:
        """out_count。"""

        return len(self.out_ports)

    @property
    def in_labels(self) -> list[str]:
        return [p.label for p in self.in_ports]

    @property
    def out_labels(self) -> list[str]:
        return [p.label for p in self.out_ports]


class PackageManager:
    """管理所有已加载的计算包。"""

    def __init__(self, auto_discover: bool = True) -> None:
        self._packages: dict[str, list[CompositeTypeDef]] = {}

        self._type_map: dict[str, CompositeTypeDef] = {}

        # 自动发现默认目录下的子图包
        if auto_discover:
            self._discover_default_packages()

    def loaded_packages(self) -> dict[str, list[CompositeTypeDef]]:
        """返回 {包名: [复合节点定义, ...]}"""

        return dict(self._packages)

    def get_type_def(self, type_id: str) -> CompositeTypeDef | None:
        """按 type_id 查找复合节点定义。"""

        return self._type_map.get(type_id)

    def get_sub_graph_doc(self, type_id: str) -> GraphDocument | None:
        """获取复合节点对应的子图文档。"""

        tdef = self._type_map.get(type_id)

        if tdef is None or not tdef.source_graph_json:
            return None

        try:
            data = json.loads(tdef.source_graph_json)

            return document_from_json(data)

        except Exception:
            return None

    def load_json(self, path: Path, package_name: str = "") -> CompositeTypeDef:
        """从 .json 文件加载一个复合节点类型。"""

        graph_json = path.read_text(encoding="utf-8")

        data = json.loads(graph_json)

        doc = document_from_json(data)

        graph_name = path.stem

        if not package_name:
            package_name = graph_name

        tdef = self._make_type_def(package_name, graph_name, path.name, graph_json, doc)

        self._register(tdef)

        return tdef

    def load_zip(self, path: Path) -> list[CompositeTypeDef]:
        """从 .zip 文件加载包（多个 .json 文件）。"""

        package_name = path.stem

        loaded: list[CompositeTypeDef] = []

        with zipfile.ZipFile(path, "r") as zf:
            for name in zf.namelist():
                if not name.endswith(".json"):
                    continue

                graph_json = zf.read(name).decode("utf-8")

                try:
                    data = json.loads(graph_json)

                    doc = document_from_json(data)

                except Exception:
                    continue

                graph_name = Path(name).stem

                tdef = self._make_type_def(package_name, graph_name, name, graph_json, doc)

                loaded.append(tdef)

        for tdef in loaded:
            self._register(tdef)

        return loaded

    def _make_type_def(
        self,
        package_name: str,
        graph_name: str,
        source_file: str,
        graph_json: str,
        doc: GraphDocument,
    ) -> CompositeTypeDef:
        """_make_type_def。"""
        type_id = f"@{package_name}/{graph_name}"

        display_name = f"[{package_name}] {graph_name}"

        in_ports: list[CompositePortDef] = []

        out_ports: list[CompositePortDef] = []

        for _i, node in enumerate(doc.nodes):
            if node.type == "user_input":
                label = node.label or node.id

                in_ports.append(CompositePortDef(label=label, node_id=node.id, port_index=0))

            elif node.type == "output":
                label = node.label or node.id

                out_ports.append(CompositePortDef(label=label, node_id=node.id, port_index=0))

        return CompositeTypeDef(
            type_id=type_id,
            display_name=display_name,
            package_name=package_name,
            source_file=source_file,
            in_ports=in_ports,
            out_ports=out_ports,
            source_graph_json=graph_json,
        )

    def _register(self, tdef: CompositeTypeDef) -> None:
        """_register。"""

        if tdef.package_name not in self._packages:
            self._packages[tdef.package_name] = []

        # 避免重复注册

        existing = [t for t in self._packages[tdef.package_name] if t.type_id == tdef.type_id]

        if not existing:
            self._packages[tdef.package_name].append(tdef)

        self._type_map[tdef.type_id] = tdef

    def _discover_default_packages(self) -> None:
        """自动发现默认目录下的子图包。"""

        packages_dir = _DEFAULT_PACKAGES_DIR

        if not packages_dir.is_dir():
            logger.debug("默认子图包目录不存在: %s", packages_dir)
            return

        logger.info("自动发现子图包目录: %s", packages_dir)

        # 扫描 .json 文件
        for json_file in packages_dir.glob("*.json"):
            try:
                self.load_json(json_file)
                logger.info("自动加载子图: %s", json_file.name)
            except Exception as e:
                logger.warning("加载子图失败 %s: %s", json_file.name, e)

        # 扫描 .zip 文件
        for zip_file in packages_dir.glob("*.zip"):
            try:
                self.load_zip(zip_file)
                logger.info("自动加载子图包: %s", zip_file.name)
            except Exception as e:
                logger.warning("加载子图包失败 %s: %s", zip_file.name, e)

    def discover_from_directory(self, directory: Path) -> int:
        """从指定目录发现并加载子图包。

        Args:
            directory: 要扫描的目录路径

        Returns:
            加载的子图/子图包数量
        """

        if not directory.is_dir():
            logger.warning("目录不存在: %s", directory)
            return 0

        count = 0

        # 扫描 .json 文件
        for json_file in directory.glob("*.json"):
            try:
                self.load_json(json_file)
                logger.info("加载子图: %s", json_file.name)
                count += 1
            except Exception as e:
                logger.warning("加载子图失败 %s: %s", json_file.name, e)

        # 扫描 .zip 文件
        for zip_file in directory.glob("*.zip"):
            try:
                self.load_zip(zip_file)
                logger.info("加载子图包: %s", zip_file.name)
                count += 1
            except Exception as e:
                logger.warning("加载子图包失败 %s: %s", zip_file.name, e)

        return count
