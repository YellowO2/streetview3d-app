"""The panoramas around one clicked spot, for the splat tab: which captures
exist at the nearest Street View node, and for each, the same capture's
nearest pano at every node it links to (DA3 runs them together, so the
splat is scaled against more than one viewpoint).

Same capture means same date: panos of different dates are never
DA3-linked (see streetview_to_3d's walk_graph). Google only.
"""
from streetview_to_3d.build_street_graph.build_graph import cap_bucket_for_date
from streetview_to_3d.build_street_graph.date_ranking import date_recency_key
from streetview_to_3d.build_street_graph.fetch_nodes import fetch_corridor_nodes
from streetview_to_3d.services.geo import haversine_m
from streetview_to_3d.services.streetview_fetch import DA3_ONLY_ZOOM, download_pano_by_id, run_async
from streetview_to_3d.ui.map_selection.candidates import nearby_nodes

# How far to look for Street View nodes around a pasted location.
NEAR_M = 60.0


def node_near(lat, lon):
    """((lat, lon), [(lat, lon), ...]): the Street View node nearest a
    location, and the nodes it links to."""
    nodes, edges = nearby_nodes(lat, lon, radius_m=NEAR_M)
    if not nodes:
        raise ValueError(f"no Street View coverage within {NEAR_M:.0f} m")
    by_key = {n["key"]: n for n in nodes}
    k = nodes[0]["key"]
    links = [b if a == k else a for a, b in edges if k in (a, b)]
    return ((nodes[0]["lat"], nodes[0]["lon"]),
            [(by_key[o]["lat"], by_key[o]["lon"]) for o in links])


def panos_around(node, neighbours):
    """node: (lat, lon) of the clicked node; neighbours: the (lat, lon) of
    each node it links to on the map.

    Returns [{"target": pano, "neighbours": [pano, ...]}, ...], one per
    capture at the node, newest first. A pano is fetch_corridor_nodes'
    dict (key, id, lat, lon, date, heading, ...). A capture with no pano
    at any neighbour -- or a node with no neighbours -- still comes back,
    with no neighbours: DA3 then has the target alone.
    """
    buckets, points, adjacency, _ = fetch_corridor_nodes(
        [(node, n) for n in neighbours] or [(node, node)])
    t = min(range(len(points)), key=lambda i: haversine_m(*node, *points[i]))

    captures = {}
    for p in sorted(buckets[t], key=lambda p: haversine_m(*node, p["lat"], p["lon"])):
        captures.setdefault(p["date"], p)

    out = []
    for date, target in sorted(captures.items(), key=lambda c: date_recency_key(c[0]), reverse=True):
        near = []
        for i in adjacency.get(t, []):
            if i != t:
                near += cap_bucket_for_date(buckets[i], date, *points[i], 1)
        out.append({"target": target, "neighbours": near})
    return out


def download(pano, full_res=False):
    """Local path of a pano from panos_around. full_res for the image a splat
    is painted from; otherwise DA3's own resolution, which is all depth uses."""
    if full_res:
        return run_async(download_pano_by_id(pano["id"]))
    return run_async(download_pano_by_id(pano["id"], zoom=DA3_ONLY_ZOOM))
