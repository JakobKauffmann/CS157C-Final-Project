import tempfile, os
from pyvis.network import Network

def graph_from_rows(rows):
    """
    Render nodes from query results.
    Each row should have an 'id' or 'userId' field.
    """
    net = Network(
        height="600px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
    )

    added = set()

    for r in rows:
        data = r.data() if hasattr(r, 'data') else r
        uid = data.get("id") or data.get("userId")
        if not uid or uid in added:
            continue
        added.add(uid)

        tooltip = (
            f"<b>ID:</b> {uid}<br>"
            f"<b>Username:</b> {data.get('username','')}<br>"
            f"<b>Name:</b> {data.get('name','')}<br>"
            f"<b>Bio:</b> {data.get('bio','')}"
        )

        net.add_node(
            uid,
            label=str(data.get('username', uid)),
            title=tooltip,
            color="#2AA4F4"
        )

    tmp = os.path.join(tempfile.gettempdir(), "graph.html")
    net.save_graph(tmp)
    return tmp


def graph_with_edges(rows, center_user=None):
    """
    Render a graph with nodes and FOLLOWS edges.
    Expects rows with: source_id, source_username, target_id, target_username
    Optional center_user dict to highlight the central node.
    """
    net = Network(
        height="600px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
        directed=True,
    )
    
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=150)

    added_nodes = set()

    # Add center user if provided
    if center_user:
        cid = center_user.get("id") or center_user.get("userId")
        if cid and cid not in added_nodes:
            net.add_node(
                cid,
                label=center_user.get("username", str(cid)),
                title=f"<b>Center User:</b> {center_user.get('username', '')}",
                color="#FF6B6B",
                size=30
            )
            added_nodes.add(cid)

    for r in rows:
        data = r.data() if hasattr(r, 'data') else r
        
        src_id = data.get("source_id") or data.get("followerId")
        src_name = data.get("source_username") or data.get("follower_username") or str(src_id)
        tgt_id = data.get("target_id") or data.get("followeeId")
        tgt_name = data.get("target_username") or data.get("followee_username") or str(tgt_id)

        # Add source node
        if src_id and src_id not in added_nodes:
            net.add_node(
                src_id,
                label=src_name,
                title=f"<b>User:</b> {src_name}",
                color="#2AA4F4",
                size=20
            )
            added_nodes.add(src_id)

        # Add target node
        if tgt_id and tgt_id not in added_nodes:
            net.add_node(
                tgt_id,
                label=tgt_name,
                title=f"<b>User:</b> {tgt_name}",
                color="#2AA4F4",
                size=20
            )
            added_nodes.add(tgt_id)

        # Add edge
        if src_id and tgt_id:
            net.add_edge(src_id, tgt_id, color="#888888", arrows="to")

    tmp = os.path.join(tempfile.gettempdir(), "graph_edges.html")
    net.save_graph(tmp)
    return tmp


def mutual_graph(rows, user_a=None, user_b=None):
    """
    Render mutual connections graph.
    Shows two users and their shared connections.
    """
    net = Network(
        height="600px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
        directed=True,
    )
    
    net.barnes_hut(gravity=-2000, central_gravity=0.5, spring_length=200)

    added_nodes = set()

    # Add user A (red)
    if user_a:
        aid = user_a.get("id")
        if aid and aid not in added_nodes:
            net.add_node(
                aid,
                label=user_a.get("username", str(aid)),
                title=f"<b>User A:</b> {user_a.get('username', '')}",
                color="#FF6B6B",
                size=35
            )
            added_nodes.add(aid)

    # Add user B (green)
    if user_b:
        bid = user_b.get("id")
        if bid and bid not in added_nodes:
            net.add_node(
                bid,
                label=user_b.get("username", str(bid)),
                title=f"<b>User B:</b> {user_b.get('username', '')}",
                color="#6BCB77",
                size=35
            )
            added_nodes.add(bid)

    # Add mutual connections (blue)
    for r in rows:
        data = r.data() if hasattr(r, 'data') else r
        mid = data.get("id") or data.get("userId")
        mname = data.get("username", str(mid))
        
        if mid and mid not in added_nodes:
            net.add_node(
                mid,
                label=mname,
                title=f"<b>Mutual:</b> {mname}",
                color="#4D96FF",
                size=25
            )
            added_nodes.add(mid)

        # Draw edges from both users to mutual
        if user_a and user_a.get("id"):
            net.add_edge(user_a["id"], mid, color="#FF6B6B", arrows="to")
        if user_b and user_b.get("id"):
            net.add_edge(user_b["id"], mid, color="#6BCB77", arrows="to")

    tmp = os.path.join(tempfile.gettempdir(), "mutual_graph.html")
    net.save_graph(tmp)
    return tmp


def recommendation_graph(rows, center_user=None):
    """
    Render friend recommendation graph.
    Shows center user, their friends, and recommended users.
    """
    net = Network(
        height="600px",
        width="100%",
        bgcolor="#222222",
        font_color="white",
        directed=True,
    )
    
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=180)

    added_nodes = set()

    # Add center user (red, large)
    if center_user:
        cid = center_user.get("id")
        if cid and cid not in added_nodes:
            net.add_node(
                cid,
                label=center_user.get("username", str(cid)),
                title=f"<b>You:</b> {center_user.get('username', '')}",
                color="#FF6B6B",
                size=40
            )
            added_nodes.add(cid)

    for r in rows:
        data = r.data() if hasattr(r, 'data') else r
        
        rec_id = data.get("id") or data.get("recommended_id")
        rec_name = data.get("username") or data.get("recommended_username") or str(rec_id)
        mutual_count = data.get("mutualCount") or data.get("mutual_count") or 0
        
        if rec_id and rec_id not in added_nodes:
            # Size based on mutual count
            size = 15 + min(mutual_count * 3, 25)
            net.add_node(
                rec_id,
                label=f"{rec_name}\n({mutual_count} mutual)",
                title=f"<b>Recommended:</b> {rec_name}<br><b>Mutual Friends:</b> {mutual_count}",
                color="#FFD93D",
                size=size
            )
            added_nodes.add(rec_id)
            
            # Draw dashed edge to represent recommendation
            if center_user and center_user.get("id"):
                net.add_edge(
                    center_user["id"], 
                    rec_id, 
                    color="#FFD93D", 
                    dashes=True,
                    title=f"{mutual_count} mutual connections"
                )

    tmp = os.path.join(tempfile.gettempdir(), "recommendation_graph.html")
    net.save_graph(tmp)
    return tmp
