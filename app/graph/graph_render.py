import tempfile, os
from pyvis.network import Network

def graph_from_rows(rows):
    net = Network(
        height="600px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
    )

    added = set()

    for r in rows:
        uid = r.get("id") or r.get("userId")
        if not uid or uid in added:
            continue
        added.add(uid)

        tooltip = (
            f"<b>ID:</b> {uid}<br>"
            f"<b>Username:</b> {r.get('username','')}<br>"
            f"<b>Name:</b> {r.get('name','')}<br>"
            f"<b>Bio:</b> {r.get('bio','')}"
        )

        net.add_node(
            uid,
            label=str(uid),
            title=tooltip,
            color="#2AA4F4"
        )

    tmp = os.path.join(tempfile.gettempdir(), "graph.html")
    net.save_graph(tmp)
    return tmp
