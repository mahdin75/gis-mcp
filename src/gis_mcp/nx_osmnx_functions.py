import os
import logging
import json
import math
import pandas as pd
import geopandas as gpd
import networkx as nx
from typing import List, Optional, Union, Dict, Any
from shapely.geometry import LineString, MultiLineString
from .mcp import gis_mcp

# Configure logging
logger = logging.getLogger(__name__)

@gis_mcp.resource("gis://operation/nx_osmnx")
def get_nx_osmnx_operations() -> Dict[str, List[str]]:
    """List available rasterio operations."""
    return {
        "operations": [
            "nx_create_graph"
        ]
    }

@gis_mcp.tool()
def nx_create_graph(
    edge_path: str,
    node_path: Optional[str] = None,
    # Column mappings (for tabular edge sources)
    source_col: str = "source",
    target_col: str = "target",
    weight_col: Optional[str] = None,
    edge_attrs: Optional[List[str]] = None,    # extra edge attribute columns to carry over
    # Node table settings (optional)
    node_id_col: str = "id",
    node_attrs: Optional[List[str]] = None,    # node attribute columns to carry over
    # Graph type
    directed: bool = False,
    multigraph: bool = False,
    allow_self_loops: bool = False,
    # Geo options (when edge_path is a spatial file with LineString/MultiLineString)
    from_geometry: bool = False,               # if True, endpoints of lines form edges
    geometry_col: str = "geometry",
    # Output (optional)
    output_path: Optional[str] = None,         # if provided, graph is serialized
    output_format: Optional[str] = None        # 'graphml' | 'gexf' | 'gpickle'
) -> Dict[str, Any]:
    """
    Create a NetworkX graph from an edge file (CSV/TSV/Excel/Parquet/Feather/JSON or Shapefile/GPKG)
    and optional node file. Returns JSON with summary stats and small previews.

    Nodes:
      - From tabular edges: values in `source_col` & `target_col`
      - From geometry edges: endpoints (x,y) tuples of each LineString/MultiLineString segment

    Edge attributes:
      - `weight_col` becomes the 'weight' attribute (float if possible)
      - Any columns listed in `edge_attrs` are carried over as attributes

    Node attributes (optional):
      - Loaded from `node_path` using `node_id_col` as the node identifier
      - Columns listed in `node_attrs` are attached to nodes
    """
    try:
        if not os.path.exists(edge_path):
            return {"status": "error", "message": f"Edge file not found: {edge_path}"}

        def _ext(p): 
            return os.path.splitext(p)[1].lower()

        # ---------- READ EDGES ----------
        edges_df = None
        gdf_edges = None
        ext = _ext(edge_path)

        # Decide parser based on extension
        tabular_exts = {".csv", ".tsv", ".txt", ".parquet", ".feather", ".json", ".xlsx"}
        geo_exts = {".shp", ".gpkg", ".geojson"}

        if from_geometry or ext in geo_exts:
            # Geo path
            gdf_edges = gpd.read_file(edge_path)
            if geometry_col not in gdf_edges.columns and gdf_edges.geometry.name:
                geometry_col = gdf_edges.geometry.name
            if geometry_col not in gdf_edges.columns:
                return {"status": "error", "message": f"Geometry column '{geometry_col}' not found in {edge_path}"}
        else:
            # Tabular path
            if ext in {".csv", ".tsv", ".txt"}:
                sep = "\t" if ext in {".tsv", ".txt"} else ","
                edges_df = pd.read_csv(edge_path, sep=sep)
            elif ext == ".xlsx":
                edges_df = pd.read_excel(edge_path)
            elif ext == ".parquet":
                edges_df = pd.read_parquet(edge_path)
            elif ext == ".feather":
                edges_df = pd.read_feather(edge_path)
            elif ext == ".json":
                # expect records or edge list; pandas will try to infer
                try:
                    edges_df = pd.read_json(edge_path, orient="records")
                except ValueError:
                    edges_df = pd.read_json(edge_path)  # fallback
            else:
                return {"status": "error", "message": f"Unsupported edge file extension: {ext}"}

        # ---------- BUILD GRAPH ----------
        if multigraph and directed:
            G: Union[nx.MultiDiGraph, nx.MultiGraph, nx.DiGraph, nx.Graph] = nx.MultiDiGraph()
        elif multigraph and not directed:
            G = nx.MultiGraph()
        elif not multigraph and directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        # Helper to add one edge
        def _add_edge(u, v, attr: Dict[str, Any]):
            if not allow_self_loops and (u == v):
                return
            # coerce weight
            if weight_col is not None:
                wval = attr.get(weight_col, None)
                if wval is not None:
                    try:
                        attr["weight"] = float(wval)
                    except Exception:
                        attr["weight"] = wval  # keep as-is if not convertible
            if not multigraph:
                attr.pop("key", None)
            G.add_edge(u, v, **attr)

        # (A) From geometry (LineString/MultiLineString)
        if gdf_edges is not None:
            # carry over selected attributes
            carry_cols = set(edge_attrs or [])
            carry_cols = [c for c in carry_cols if c in gdf_edges.columns and c != geometry_col]
            for _, row in gdf_edges.iterrows():
                geom = row[geometry_col]
                if isinstance(geom, LineString):
                    coords = list(geom.coords)
                    if len(coords) >= 2:
                        u = (coords[0][0], coords[0][1])
                        v = (coords[-1][0], coords[-1][1])
                        attr = {c: row[c] for c in carry_cols}
                        if weight_col and weight_col in row.index:
                            attr[weight_col] = row[weight_col]
                        _add_edge(u, v, attr)
                elif isinstance(geom, MultiLineString):
                    for part in geom.geoms:
                        coords = list(part.coords)
                        if len(coords) >= 2:
                            u = (coords[0][0], coords[0][1])
                            v = (coords[-1][0], coords[-1][1])
                            attr = {c: row[c] for c in carry_cols}
                            if weight_col and weight_col in row.index:
                                attr[weight_col] = row[weight_col]
                            _add_edge(u, v, attr)
                else:
                    # ignore non-line geometries
                    continue

        # (B) From tabular (source/target)
        if edges_df is not None:
            miss = [c for c in [source_col, target_col] if c not in edges_df.columns]
            if miss:
                return {"status": "error", "message": f"Missing columns in edge table: {miss}"}

            carry_cols = set(edge_attrs or [])
            # ensure weight_col included too so we can coerce
            if weight_col:
                carry_cols.add(weight_col)
            carry_cols = [c for c in carry_cols if c in edges_df.columns and c not in (source_col, target_col)]

            for _, row in edges_df.iterrows():
                u = row[source_col]
                v = row[target_col]
                attr = {c: row[c] for c in carry_cols}
                _add_edge(u, v, attr)

        # ---------- NODE ATTRIBUTES (optional) ----------
        if node_path:
            if not os.path.exists(node_path):
                return {"status": "error", "message": f"Node file not found: {node_path}"}
            extn = _ext(node_path)
            if extn in {".csv", ".tsv", ".txt"}:
                sep = "\t" if extn in {".tsv", ".txt"} else ","
                nodes_df = pd.read_csv(node_path, sep=sep)
            elif extn == ".xlsx":
                nodes_df = pd.read_excel(node_path)
            elif extn == ".parquet":
                nodes_df = pd.read_parquet(node_path)
            elif extn == ".feather":
                nodes_df = pd.read_feather(node_path)
            elif extn == ".json":
                try:
                    nodes_df = pd.read_json(node_path, orient="records")
                except ValueError:
                    nodes_df = pd.read_json(node_path)
            elif extn in {".shp", ".gpkg", ".geojson"}:
                nodes_df = gpd.read_file(node_path)
            else:
                return {"status": "error", "message": f"Unsupported node file extension: {extn}"}

            if node_id_col not in nodes_df.columns:
                return {"status": "error", "message": f"node_id_col '{node_id_col}' not found in node table."}

            # pick attrs
            nattrs = [c for c in (node_attrs or []) if c in nodes_df.columns and c != node_id_col]
            for _, row in nodes_df.iterrows():
                nid = row[node_id_col]
                attrs = {c: row[c] for c in nattrs}
                if isinstance(nodes_df, gpd.GeoDataFrame) and nodes_df.geometry.name in nodes_df.columns:
                    geom = row[nodes_df.geometry.name]
                    if geom is not None:
                        attrs["geometry_wkt"] = getattr(geom, "wkt", None)
                if nid in G:  # only set attributes for nodes present in G
                    nx.set_node_attributes(G, {nid: attrs})

        # ---------- SUMMARY ----------
        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        is_dir = nx.is_directed(G)
        # self-loops
        if multigraph:
            self_loops = sum(1 for u, v, _k in G.edges(keys=True) if u == v)
        else:
            self_loops = nx.number_of_selfloops(G)

        # degrees
        degs = dict(G.degree())
        avg_deg = float(sum(degs.values()) / n_nodes) if n_nodes else 0.0
        density = float(nx.density(G)) if n_nodes else 0.0

        # components
        if is_dir:
            wcc = [len(c) for c in nx.weakly_connected_components(G)]
            scc = [len(c) for c in nx.strongly_connected_components(G)]
            comp_info = {
                "weak_components": {"count": len(wcc), "largest": max(wcc) if wcc else 0},
                "strong_components": {"count": len(scc), "largest": max(scc) if scc else 0},
            }
            isolates = list(nx.isolates(G))
        else:
            cc = [len(c) for c in nx.connected_components(G)] if n_nodes else []
            comp_info = {"components": {"count": len(cc), "largest": max(cc) if cc else 0}}
            isolates = list(nx.isolates(G))

        # Previews
        edge_preview = []
        if multigraph:
            for u, v, k, d in list(G.edges(keys=True, data=True))[:5]:
                item = {"u": u, "v": v, "key": k}
                item.update({k2: d[k2] for k2 in d})
                edge_preview.append(item)
        else:
            for u, v, d in list(G.edges(data=True))[:5]:
                item = {"u": u, "v": v}
                item.update({k2: d[k2] for k2 in d})
                edge_preview.append(item)

        node_preview = []
        for n, d in list(G.nodes(data=True))[:5]:
            item = {"id": n}
            item.update({k2: d[k2] for k2 in d})
            item["degree"] = degs.get(n, 0)
            node_preview.append(item)

        # ---------- SAVE (optional) ----------
        saved_to = None
        if output_path and output_format:
            fmt = output_format.lower()
            try:
                if fmt == "graphml":
                    nx.write_graphml(G, output_path)
                elif fmt == "gexf":
                    nx.write_gexf(G, output_path)
                elif fmt == "gpickle":
                    nx.write_gpickle(G, output_path)
                else:
                    return {"status": "error", "message": f"Unknown output_format: {output_format}"}
                saved_to = output_path
            except Exception as e:
                return {"status": "error", "message": f"Failed to save graph ({output_format}): {str(e)}"}

        # ---------- RESULT ----------
        result = {
            "graph_type": ("Multi" if multigraph else "") + ("DiGraph" if directed else "Graph"),
            "n_nodes": int(n_nodes),
            "n_edges": int(n_edges),
            "is_directed": bool(is_dir),
            "self_loops": int(self_loops),
            "isolates_count": int(len(isolates)),
            "density": density,
            "avg_degree": avg_deg,
            "components": comp_info,
            "edge_preview": edge_preview,
            "node_preview": node_preview,
            "saved_to": saved_to
        }
        return {"status": "success", "message": "Graph created successfully", "result": result}

    except Exception as e:
        return {"status": "error", "message": f"Failed to create graph: {str(e)}"}



import os, json
import networkx as nx
from typing import Any, Dict, List, Optional, Union

def nx_manipulate_graph(
    input_path: str,
    operations: List[Dict[str, Any]],   # ordered list of ops (see below)
    output_path: Optional[str] = None,  # if provided, graph is saved
    output_format: Optional[str] = None # 'graphml'|'gexf'|'gpickle'
) -> Dict[str, Any]:
    """
    Manipulate a NetworkX graph by applying a sequence of operations.

    Supported operations (op field):
      - 'add_nodes': {'nodes': [id|{id, attrs}], 'default_attrs': {...}?}
      - 'add_edges': {'edges': [(u,v)|{u,v,attrs}], 'default_attrs': {...}?}
      - 'remove_nodes': {'nodes': [ids]}
      - 'remove_edges': {'edges': [(u,v)|(u,v,key)]}
      - 'set_node_attrs': {'attrs': {node: {k:v,...}, ...}}
      - 'set_edge_attrs': {'attrs': [{u,v,attrs}|{u,v,key,attrs}, ...]}
      - 'relabel_nodes': {'mapping': {old:new}, 'copy': False}
      - 'induced_subgraph': {'nodes': [ids]}
      - 'filter_nodes': {'keep_if': {'attr': 'degree|attribute', 'op': '>=', 'value': X}}
      - 'largest_component': {'strong': False}  # for DiGraph, strong vs weak
      - 'to_undirected': {}
      - 'to_directed': {}
      - 'reverse': {'copy': True}
      - 'simplify_multigraph': {'aggregate': {'weight': 'sum'|'mean'|'max'|...}}
      - 'contract_nodes': {'mapping': {node: group_id}, 'aggregate': {'weight':'sum', ...}}
    """
    try:
        if not os.path.exists(input_path):
            return {"status": "error", "message": f"Input graph not found: {input_path}"}

        # ---- load ----
        ext = os.path.splitext(input_path)[1].lower()
        if ext == ".graphml":
            G = nx.read_graphml(input_path)
        elif ext == ".gexf":
            G = nx.read_gexf(input_path)
        elif ext in {".gpickle", ".pickle"}:
            G = nx.read_gpickle(input_path)
        else:
            return {"status": "error", "message": f"Unsupported input format: {ext}"}

        def _is_multi(G): return G.is_multigraph()

        # ---- helpers ----
        def _apply_add_nodes(op):
            nodes = op.get("nodes", [])
            default = op.get("default_attrs", {}) or {}
            for item in nodes:
                if isinstance(item, dict) and "id" in item:
                    nid = item["id"]; attrs = {**default, **{k:v for k,v in item.items() if k!='id'}}
                else:
                    nid = item; attrs = dict(default)
                G.add_node(nid, **attrs)

        def _apply_add_edges(op):
            edges = op.get("edges", [])
            default = op.get("default_attrs", {}) or {}
            for item in edges:
                if isinstance(item, dict):
                    u = item["u"]; v = item["v"]
                    attrs = {**default, **{k:v for k,v in item.items() if k not in ("u","v","key")}}
                    if _is_multi(G) and "key" in item:
                        G.add_edge(u, v, key=item["key"], **attrs)
                    else:
                        G.add_edge(u, v, **attrs)
                else:
                    # tuple (u,v) or (u,v,key)
                    if _is_multi(G) and isinstance(item, (tuple, list)) and len(item)==3:
                        u,v,k = item; G.add_edge(u,v,key=k, **default)
                    else:
                        u,v = item; G.add_edge(u,v, **default)

        def _apply_remove_nodes(op):
            for n in op.get("nodes", []):
                if G.has_node(n): G.remove_node(n)

        def _apply_remove_edges(op):
            for e in op.get("edges", []):
                if _is_multi(G) and isinstance(e, (tuple,list)) and len(e)==3:
                    u,v,k = e
                    if G.has_edge(u,v,k): G.remove_edge(u,v,k)
                else:
                    u,v = e
                    if G.has_edge(u,v): G.remove_edge(u,v)

        def _apply_set_node_attrs(op):
            for n, attrs in (op.get("attrs") or {}).items():
                if G.has_node(n): G.nodes[n].update(attrs)

        def _apply_set_edge_attrs(op):
            for rec in (op.get("attrs") or []):
                u = rec.get("u"); v = rec.get("v"); attrs = rec.get("attrs", {})
                if _is_multi(G) and "key" in rec:
                    k = rec["key"]
                    if G.has_edge(u,v,k): G.edges[u,v,k].update(attrs)
                else:
                    if G.has_edge(u,v): G.edges[u,v].update(attrs)

        def _apply_relabel(op):
            nonlocal G
            mapping = op.get("mapping", {})
            copy = bool(op.get("copy", False))
            G = nx.relabel_nodes(G, mapping, copy=copy)

        def _apply_induced(op):
            nonlocal G
            nodes = [n for n in op.get("nodes", []) if G.has_node(n)]
            nonlocal G
            G = G.subgraph(nodes).copy()

        def _apply_filter_nodes(op):
            nonlocal G
            rule = op.get("keep_if", {})
            attr = rule.get("attr")
            oper = rule.get("op", "==")
            val  = rule.get("value")
            keep=set()
            if attr == "degree":
                deg = dict(G.degree())
                for n,d in deg.items():
                    if eval(f"d {oper} {val}"): keep.add(n)
            else:
                for n,data in G.nodes(data=True):
                    x = data.get(attr, None)
                    try:
                        if eval(f"x {oper} {repr(val)}"): keep.add(n)
                    except Exception:
                        pass
            G = G.subgraph(keep).copy()

        def _apply_largest_component(op):
            nonlocal G
            strong = bool(op.get("strong", False))
            nonlocal G
            if G.is_directed():
                comps = list(nx.strongly_connected_components(G)) if strong else list(nx.weakly_connected_components(G))
            else:
                comps = list(nx.connected_components(G))
            if comps:
                biggest = max(comps, key=len)
                G = G.subgraph(biggest).copy()

        def _apply_to_undirected(_): 
            nonlocal G
            nonlocal G; G = G.to_undirected().copy()

        def _apply_to_directed(_): 
            nonlocal G
            nonlocal G; G = G.to_directed().copy()

        def _apply_reverse(op):
            nonlocal G
            copy = bool(op.get("copy", True))
            nonlocal G; G = G.reverse(copy=copy)

        def _aggregate(values, how):
            nonlocal G
            import statistics
            if how == "sum": return sum(values)
            if how == "mean": return statistics.fmean(values) if values else 0.0
            if how == "max": return max(values)
            if how == "min": return min(values)
            if how == "first": return values[0]
            if how == "last": return values[-1]
            return values[-1]  # default

        def _apply_simplify_multigraph(op):
            nonlocal G
            if not _is_multi(G): return
            agg = op.get("aggregate", {})  # {'weight':'sum', 'capacity':'max', ...}
            H = nx.DiGraph() if G.is_directed() else nx.Graph()
            H.add_nodes_from(G.nodes(data=True))
            for u,v,data in G.edges(data=True):
                key = (u,v) if not G.is_directed() else (u,v)
                if H.has_edge(u,v):
                    # merge attributes
                    for a, how in agg.items():
                        vals = H.edges[u,v].get(a, [])
                        if not isinstance(vals, list): vals = [vals]
                        vals.append(data.get(a))
                        H.edges[u,v][a] = _aggregate([x for x in vals if x is not None], how)
                else:
                    H.add_edge(u,v, **{a: data.get(a) for a in set(agg.keys()).union(data.keys())})
                    # initialize aggregated fields
                    for a, how in agg.items():
                        val = data.get(a)
                        H.edges[u,v][a] = val
            G = H

        def _apply_contract_nodes(op):
            nonlocal G
            mapping = op.get("mapping", {})  # {node: group_id}
            agg = op.get("aggregate", {})    # edge attr aggregation rules
            # contract by mapping, then simplify multiedges by agg
            nonlocal G
            H = nx.contracted_nodes if False else None  # placeholder (we'll use relabel + merge)
            # Relabel nodes to group ids
            G = nx.relabel_nodes(G, mapping, copy=False)
            # After relabel, parallel edges can exist → convert to Multi, then simplify
            G = nx.MultiDiGraph(G) if G.is_directed() else nx.MultiGraph(G)
            _apply_simplify_multigraph({"aggregate": agg})

        # ---- dispatch table ----
        handlers = {
            "add_nodes": _apply_add_nodes,
            "add_edges": _apply_add_edges,
            "remove_nodes": _apply_remove_nodes,
            "remove_edges": _apply_remove_edges,
            "set_node_attrs": _apply_set_node_attrs,
            "set_edge_attrs": _apply_set_edge_attrs,
            "relabel_nodes": _apply_relabel,
            "induced_subgraph": _apply_induced,
            "filter_nodes": _apply_filter_nodes,
            "largest_component": _apply_largest_component,
            "to_undirected": _apply_to_undirected,
            "to_directed": _apply_to_directed,
            "reverse": _apply_reverse,
            "simplify_multigraph": _apply_simplify_multigraph,
            "contract_nodes": _apply_contract_nodes,
        }

        # ---- apply operations ----
        for op in (operations or []):
            kind = op.get("op")
            fn = handlers.get(kind)
            if not fn:
                return {"status":"error","message":f"Unknown operation: {kind}"}
            fn(op)

        # ---- summary & previews ----
        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        density = float(nx.density(G)) if n_nodes else 0.0
        degs = dict(G.degree())
        avg_deg = float(sum(degs.values())/n_nodes) if n_nodes else 0.0
        isolates = list(nx.isolates(G))
        is_dir = G.is_directed()

        if is_dir:
            wcc = [len(c) for c in nx.weakly_connected_components(G)]
            comps = {"weak_components": {"count": len(wcc), "largest": max(wcc) if wcc else 0}}
        else:
            cc = [len(c) for c in nx.connected_components(G)] if n_nodes else []
            comps = {"components": {"count": len(cc), "largest": max(cc) if cc else 0}}

        edge_preview = []
        if _is_multi(G):
            for u,v,k,d in list(G.edges(keys=True, data=True))[:5]:
                row = {"u":u,"v":v,"key":k}; row.update(d); edge_preview.append(row)
        else:
            for u,v,d in list(G.edges(data=True))[:5]:
                row = {"u":u,"v":v}; row.update(d); edge_preview.append(row)

        node_preview = []
        for n,d in list(G.nodes(data=True))[:5]:
            row = {"id":n,"degree":degs.get(n,0)}; row.update(d); node_preview.append(row)

        # ---- save (optional) ----
        saved_to = None
        if output_path and output_format:
            fmt = (output_format or "").lower()
            if fmt == "graphml":
                nx.write_graphml(G, output_path)
            elif fmt == "gexf":
                nx.write_gexf(G, output_path)
            elif fmt == "gpickle":
                nx.write_gpickle(G, output_path)
            else:
                return {"status":"error","message":f"Unknown output_format: {output_format}"}
            saved_to = output_path

        result = {
            "n_nodes": int(n_nodes),
            "n_edges": int(n_edges),
            "is_directed": bool(is_dir),
            "density": density,
            "avg_degree": avg_deg,
            "isolates_count": int(len(isolates)),
            "components": comps,
            "node_preview": node_preview,
            "edge_preview": edge_preview,
            "saved_to": saved_to
        }
        return {"status":"success","message":"Graph manipulated successfully","result":result}

    except Exception as e:
        return {"status":"error","message":f"Failed to manipulate graph: {str(e)}"}

