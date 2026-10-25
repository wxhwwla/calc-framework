# -*- coding: utf-8 -*-
from calc_framework.config.adapter import AdapterPackage

pkg = AdapterPackage("framework/adapters/genshin_like")
print(f"适配器: {pkg.meta['name']}")
print(f"DAG 节点数: {len(pkg.dag_service.dag.nodes)}")
print(f"DAG 输出数: {len(pkg.dag_service.dag.outputs)}")
