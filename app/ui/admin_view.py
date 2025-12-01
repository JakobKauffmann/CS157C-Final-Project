import streamlit as st
from ui.components import two_panel_query_ui, dataframe
from graph.graph_render import graph_from_rows, mutual_graph, recommendation_graph
from db.neo4j_client import run_query
import bcrypt


def render_admin_view():
    st.header("Admin Dashboard")
    st.divider()

    # ======================================================
    # UC-1: User Registration
    # ======================================================
    st.subheader("UC-1: User Registration")
    st.write("Register a new user by providing basic details. The system stores user data in Neo4j as nodes.")

    col1, col2 = st.columns(2)

    with col1:
        new_username = st.text_input("Username", key="uc1_username", placeholder="e.g., CoolUser123")
        new_email = st.text_input("Email", key="uc1_email", placeholder="e.g., user@example.com")
        new_name = st.text_input("Full Name", key="uc1_name", placeholder="e.g., John Doe")

    with col2:
        new_bio = st.text_area("Bio", key="uc1_bio", placeholder="Tell us about yourself...", height=100)
        new_password = st.text_input("Password", type="password", key="uc1_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="uc1_confirm")

    cypher_query = f"""
// UC-1: User Registration
// Creates a new User node with provided details
// Password is stored as a bcrypt hash for security
CREATE (u:User {{
    userId: $userId,
    username: '{new_username if new_username else "<enter username>"}',
    email: '{new_email if new_email else "<enter email>"}',
    name: '{new_name if new_name else "<enter name>"}',
    bio: '{new_bio if new_bio else "<enter bio>"}',
    passwordHash: $passwordHash
}})
RETURN
    u.userId AS id,
    u.username AS username,
    u.email AS email,
    u.name AS name,
    u.bio AS bio,
    'CREATED' AS status
"""

    st.write("### Cypher Query ")
    st.code(cypher_query, language="cypher")

    col_a, col_b = st.columns([1, 3])

    with col_a:
        if st.button("Register User", key="uc1_register"):
            # Validation
            if not all([new_username, new_email, new_name, new_password]):
                st.error("Please fill in all required fields (Username, Email, Name, Password).")
            elif new_password != confirm_password:
                st.error("Passwords do not match!")
            elif len(new_password) < 4:
                st.error("Password must be at least 4 characters")
            else:
                # Check if username already exists
                existing = run_query(
                    """
                    MATCH (u:User {username: $username})
                    RETURN u.username AS username
                """,
                    {"username": new_username},
                )

                if existing:
                    st.error(f"Username '{new_username}' is already taken!")
                else:
                    # Check if email already exists
                    existing_email = run_query(
                        """
                        MATCH (u:User {email: $email})
                        RETURN u.email AS email
                    """,
                        {"email": new_email},
                    )

                    if existing_email:
                        st.error(f"Email '{new_email}' is already registered!")
                    else:
                        # Generate new user ID
                        max_id_result = run_query("""
                            MATCH (u:User)
                            RETURN max(toInteger(u.userId)) AS maxId
                        """)
                        max_id = (max_id_result[0].data()["maxId"] if max_id_result else 0)
                        new_id = f"{(max_id or 0) + 1:04d}"

                        # Hash password
                        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

                        # Create user
                        result = run_query(
                            """
                            CREATE (u:User {
                                userId: $userId,
                                username: $username,
                                email: $email,
                                name: $name,
                                bio: $bio,
                                passwordHash: $passwordHash
                            })
                            RETURN
                                u.userId AS id,
                                u.username AS username,
                                u.email AS email,
                                u.name AS name,
                                u.bio AS bio
                        """,
                            {
                                "userId": new_id,
                                "username": new_username,
                                "email": new_email,
                                "name": new_name,
                                "bio": new_bio or f"Hello, I'm {new_name}!",
                                "passwordHash": password_hash,
                            },
                        )

                        if result:
                            st.success(f"✅ User '{new_username}' registered successfully with ID: {new_id}")
                            df = dataframe(result)
                            st.dataframe(df, use_container_width=True)
    st.divider()

    # ======================================================
    # UC-2: User Login
    # ======================================================
    st.subheader("UC-2: User Login")
    st.write("Authenticate a user with username and password. The system verifies credentials against stored data.")

    col1, col2 = st.columns(2)

    with col1:
        login_username = st.text_input("Username", key="uc2_username", placeholder="Enter username")

    with col2:
        login_password = st.text_input("Password", type="password", key="uc2_password", placeholder="Enter password")

    cypher_query = f"""
// UC-2: User Login
// Retrieves user by username for authentication

MATCH (u:User {{username: '{login_username if login_username else "<enter username>"}'}})
RETURN
    u.userId AS id,
    u.username AS username,
    u.email AS email,
    u.name AS name,
    u.bio AS bio,
    u.passwordHash AS passwordHash
"""

    st.write("### Cypher Query")
    st.code(cypher_query, language="cypher")

    col_a, col_b = st.columns([1, 1])

    with col_a:
        if st.button("Login", key="uc2_login"):
            if not login_username or not login_password:
                st.error("Please enter both username and password")
            else:
                result = run_query(
                    """
                    MATCH (u:User {username: $username})
                    RETURN
                        u.userId AS id,
                        u.username AS username,
                        u.email AS email,
                        u.name AS name,
                        u.bio AS bio,
                        u.passwordHash AS passwordHash
                """,
                    {"username": login_username},
                )

                if not result:
                    st.error(f"❌ User '{login_username}' not found!")
                else:
                    user_data = result[0].data()
                    stored_hash = user_data["passwordHash"]

                    if bcrypt.checkpw(login_password.encode(), stored_hash.encode()):
                        st.success(f"✅ Login successful! Welcome, {user_data['name']}!")

                        # Show user info (without password hash)
                        display_data = {k: v for k, v in user_data.items() if k != "passwordHash"}
                        st.write("### Authenticated User Info")
                        st.json(display_data)
                    else:
                        st.error("❌ Invalid password!")

    with col_b:
        if st.button("Check User Exists", key="uc2_check"):
            if login_username:
                result = run_query(
                    """
                    MATCH (u:User {username: $username})
                    RETURN u.username AS username, u.name AS name
                """,
                    {"username": login_username},
                )

                if result:
                    st.success(f"✅ User '{login_username}' exists")
                else:
                    st.warning(f"❌ User '{login_username}' not found")
    st.divider()

    # ======================================================
    # UC-3: View Profile
    # ======================================================
    st.subheader("UC-3: View Profile")
    st.write("View a user's profile information including their details and social statistics.")

    # Load all users for dropdown
    users = run_query("""
        MATCH (u:User)
        RETURN u.userId AS id, u.username AS username
        ORDER BY u.username
        LIMIT 500
    """)

    user_list = [f"{r.data()['username']} ({r.data()['id']})" for r in users]
    user_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in users}

    selected_label = st.selectbox("Select User to View", user_list, key="uc3_user")

    if selected_label:
        selected_user = user_map[selected_label]
        uid = selected_user["id"]

        cypher_query = f"""
// UC-3: View Profile
// Retrieves complete user profile with social statistics

MATCH (u:User {{userId: '{uid}'}})
OPTIONAL MATCH (u)<-[:FOLLOWS]-(follower)
WITH u, count(DISTINCT follower) AS followerCount
OPTIONAL MATCH (u)-[:FOLLOWS]->(following)
RETURN
    u.userId AS id,
    u.username AS username,
    u.email AS email,
    u.name AS name,
    u.bio AS bio,
    followerCount,
    count(DISTINCT following) AS followingCount
"""

        st.write("### Cypher Query")
        st.code(cypher_query, language="cypher")

        if st.button("View Profile", key="uc3_view"):
            result = run_query(
                """
                MATCH (u:User {userId: $uid})
                OPTIONAL MATCH (u)<-[:FOLLOWS]-(follower)
                WITH u, count(DISTINCT follower) AS followerCount
                OPTIONAL MATCH (u)-[:FOLLOWS]->(following)
                RETURN
                    u.userId AS id,
                    u.username AS username,
                    u.email AS email,
                    u.name AS name,
                    u.bio AS bio,
                    followerCount,
                    count(DISTINCT following) AS followingCount
            """,
                {"uid": uid},
            )

            if result:
                profile = result[0].data()

                st.write("### Profile Information")

                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**Username:** {profile['username']}")
                    st.write(f"**Name:** {profile['name']}")
                    st.write(f"**Email:** {profile['email']}")
                    st.write(f"**Bio:** {profile['bio']}")
                    st.write(f"**User ID:** {profile['id']}")

                with col2:
                    st.metric("Followers", profile["followerCount"])

                with col3:
                    st.metric("Following", profile["followingCount"])

                st.write("### Raw Data")
                df = dataframe(result)
                st.dataframe(df, use_container_width=True)
    st.divider()

    # ======================================================
    # UC-4: Edit Profile
    # ======================================================
    st.subheader("UC-4: Edit Profile")
    st.write("Update a user's profile information (name, bio, email).")

    # Load all users for dropdown
    users = run_query("""
        MATCH (u:User)
        RETURN u.userId AS id, u.username AS username, u.name AS name,
               u.email AS email, u.bio AS bio
        ORDER BY u.username
        LIMIT 500
    """)

    user_list = [f"{r.data()['username']} ({r.data()['id']})" for r in users]
    user_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in users}

    selected_label = st.selectbox("Select User to Edit", user_list, key="uc4_user")

    if selected_label:
        selected_user = user_map[selected_label]
        uid = selected_user["id"]

        st.write(f"### Editing Profile for: **{selected_user['username']}**")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Current Values:**")
            st.write(f"- Name: {selected_user['name']}")
            st.write(f"- Email: {selected_user['email']}")
            st.write(f"- Bio: {selected_user['bio']}")

        with col2:
            st.write("**New Values:**")
            new_name = st.text_input("New Name", value=selected_user["name"], key="uc4_name")
            new_email = st.text_input("New Email", value=selected_user["email"], key="uc4_email")
            new_bio = st.text_area("New Bio", value=selected_user["bio"], key="uc4_bio", height=100)

        cypher_query = f"""
// UC-4: Edit Profile
// Updates user profile information

MATCH (u:User {{userId: '{uid}'}})
SET u.name = '{new_name}',
    u.email = '{new_email}',
    u.bio = '{new_bio}'
RETURN
    u.userId AS id,
    u.username AS username,
    u.email AS email,
    u.name AS name,
    u.bio AS bio,
    'UPDATED' AS status
"""

        st.write("### Cypher Query")
        st.code(cypher_query, language="cypher")

        col_a, col_b = st.columns([1, 3])

        with col_a:
            if st.button("Save Changes", key="uc4_save"):
                # Validate email uniqueness (if changed)
                if new_email != selected_user["email"]:
                    existing_email = run_query(
                        """
                        MATCH (u:User {email: $email})
                        WHERE u.userId <> $uid
                        RETURN u.email AS email
                    """,
                        {"email": new_email, "uid": uid},
                    )

                    if existing_email:
                        st.error(f"Email '{new_email}' is already in use by another user!")
                        return

                # Update profile
                result = run_query(
                    """
                    MATCH (u:User {userId: $uid})
                    SET u.name = $newName,
                        u.email = $newEmail,
                        u.bio = $newBio
                    RETURN
                        u.userId AS id,
                        u.username AS username,
                        u.email AS email,
                        u.name AS name,
                        u.bio AS bio
                """,
                    {
                        "uid": uid,
                        "newName": new_name,
                        "newEmail": new_email,
                        "newBio": new_bio,
                    },
                )

                if result:
                    st.success("✅ Profile updated successfully!")

                    st.write("### Updated Profile")
                    df = dataframe(result)
                    st.dataframe(df, use_container_width=True)

        with col_b:
            if st.button("Reset", key="uc4_reset"):
                st.rerun()
    st.divider()

    # ======================================================
    # UC-5: Follow Another User (Jakob)
    # ======================================================
    render_uc5_follow_user()
    st.divider()

    # ======================================================
    # UC-6: Unfollow a User (Jakob)
    # ======================================================
    render_uc6_unfollow_user()
    st.divider()

    # ======================================================
    # UC-7: View Friends/Connections (Jakob)
    # ======================================================
    render_uc7_view_connections()
    st.divider()

    # ======================================================
    # UC-8: Mutual Connections (Jakob)
    # ======================================================
    render_uc8_mutual_connections()
    st.divider()

    # ======================================================
    # UC-9: Friend Recommendations (Jakob)
    # ======================================================
    render_uc9_friend_recommendations()
    st.divider()



    # ======================================================
    # UC-10 Search Users
    # ======================================================
    q = st.text_input("Search Term")
    uc10 = """
    MATCH (u:User)
    WHERE toLower(u.username) CONTAINS toLower($q)
       OR toLower(u.name) CONTAINS toLower($q)
    RETURN u.userId AS id, u.username, u.name, u.bio
    LIMIT 50
    """
    two_panel_query_ui("UC-10: Search Users", uc10, params={"q": q})

    # ======================================================
    # UC-11 Popular Users
    # ======================================================
    uc11 = """
    MATCH (u:User)
    OPTIONAL MATCH (u)<-[:FOLLOWS]-(f)
    WITH u, count(f) AS followerCount
    RETURN u.userId AS id, u.username AS username, u.name AS name, followerCount
    ORDER BY followerCount DESC
    LIMIT 20
    """
    two_panel_query_ui("UC-11: Popular Users", uc11)

# ==============================================================================
# UC-5: Follow Another User (Jakob)
# ==============================================================================
def render_uc5_follow_user():
    st.subheader("UC-5: Follow Another User")
    st.write("Select a user (follower) who will follow another user (target).")
    st.write("This creates a `FOLLOWS` relationship in the graph database.")

    users = run_query("""
        MATCH (u:User)
        RETURN u.userId AS id, u.username AS username
        ORDER BY u.username
        LIMIT 500
    """)

    user_list = [f"{r.data()['username']} ({r.data()['id']})" for r in users]
    user_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in users}

    col1, col2 = st.columns(2)

    with col1:
        follower_label = st.selectbox("Follower (who will follow)", user_list, key="uc5_follower")

    with col2:
        target_label = st.selectbox("Target (who to follow)", user_list, key="uc5_target")

    if follower_label and target_label:
        follower = user_map[follower_label]
        target = user_map[target_label]

        cypher_query = f"""
// UC-5: Follow Another User
// Creates a FOLLOWS relationship between two users

MATCH (follower:User {{userId: '{follower['id']}'}})
MATCH (target:User {{userId: '{target['id']}'}})
MERGE (follower)-[r:FOLLOWS]->(target)
RETURN
    follower.userId AS followerId,
    follower.username AS followerUsername,
    target.userId AS targetId,
    target.username AS targetUsername,
    type(r) AS relationship
"""

        st.write("### Cypher Query")
        st.code(cypher_query, language="cypher")

        col_a, col_b = st.columns([1, 3])

        with col_a:
            if st.button("Execute Follow", key="uc5_execute"):
                if follower['id'] == target['id']:
                    st.error("A user cannot follow themselves!")
                else:
                    check = run_query("""
                        MATCH (a:User {userId: $fid})-[r:FOLLOWS]->(b:User {userId: $tid})
                        RETURN count(r) AS exists
                    """, {"fid": follower['id'], "tid": target['id']})

                    if check and check[0].data()['exists'] > 0:
                        st.warning(f"{follower['username']} already follows {target['username']}!")
                    else:
                        result = run_query("""
                            MATCH (follower:User {userId: $fid})
                            MATCH (target:User {userId: $tid})
                            CREATE (follower)-[r:FOLLOWS]->(target)
                            RETURN
                                follower.userId AS followerId,
                                follower.username AS followerUsername,
                                target.userId AS targetId,
                                target.username AS targetUsername
                        """, {"fid": follower['id'], "tid": target['id']})

                        if result:
                            st.success(f"✅ {follower['username']} now follows {target['username']}!")
                            st.dataframe(dataframe(result), use_container_width=True)

        with col_b:
            if st.button("Check Status", key="uc5_check"):
                check = run_query("""
                    MATCH (a:User {userId: $fid})-[r:FOLLOWS]->(b:User {userId: $tid})
                    RETURN a.username AS follower, b.username AS following
                """, {"fid": follower['id'], "tid": target['id']})

                if check:
                    st.success(f"✅ Relationship exists: {follower['username']} → {target['username']}")
                else:
                    st.info(f"No relationship: {follower['username']} does not follow {target['username']}")


# ==============================================================================
# UC-6: Unfollow a User (Jakob)
# ==============================================================================
def render_uc6_unfollow_user():
    st.subheader("UC-6: Unfollow a User")
    st.write("Select a user (follower) who will unfollow another user (target).")
    st.write("This removes the `FOLLOWS` relationship from the graph database.")

    users = run_query("""
        MATCH (u:User)
        RETURN u.userId AS id, u.username AS username
        ORDER BY u.username
        LIMIT 500
    """)

    user_list = [f"{r.data()['username']} ({r.data()['id']})" for r in users]
    user_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in users}

    col1, col2 = st.columns(2)

    with col1:
        follower_label = st.selectbox("Follower (who is following)", user_list, key="uc6_follower")

    with col2:
        target_label = st.selectbox("Target (who to unfollow)", user_list, key="uc6_target")

    if follower_label and target_label:
        follower = user_map[follower_label]
        target = user_map[target_label]

        cypher_query = f"""
// UC-6: Unfollow a User
// Removes the FOLLOWS relationship between two users

MATCH (follower:User {{userId: '{follower['id']}'}})-[r:FOLLOWS]->(target:User {{userId: '{target['id']}'}})
DELETE r
RETURN
    follower.userId AS followerId,
    follower.username AS followerUsername,
    target.userId AS targetId,
    target.username AS targetUsername,
    'DELETED' AS status
"""

        st.write("### Cypher Query")
        st.code(cypher_query, language="cypher")

        col_a, col_b = st.columns([1, 3])

        with col_a:
            if st.button("Execute Unfollow", key="uc6_execute"):
                check = run_query("""
                    MATCH (a:User {userId: $fid})-[r:FOLLOWS]->(b:User {userId: $tid})
                    RETURN count(r) AS exists
                """, {"fid": follower['id'], "tid": target['id']})

                if not check or check[0].data()['exists'] == 0:
                    st.warning(f"{follower['username']} is not following {target['username']}!")
                else:
                    run_query("""
                        MATCH (follower:User {userId: $fid})-[r:FOLLOWS]->(target:User {userId: $tid})
                        DELETE r
                    """, {"fid": follower['id'], "tid": target['id']})
                    st.success(f"✅ {follower['username']} unfollowed {target['username']}!")

        with col_b:
            if st.button("Check Status", key="uc6_check"):
                check = run_query("""
                    MATCH (a:User {userId: $fid})-[r:FOLLOWS]->(b:User {userId: $tid})
                    RETURN a.username AS follower, b.username AS following
                """, {"fid": follower['id'], "tid": target['id']})

                if check:
                    st.success(f"✅ Relationship exists: {follower['username']} → {target['username']}")
                else:
                    st.info(f"No relationship: {follower['username']} does not follow {target['username']}")


# ==============================================================================
# UC-7: View Friends/Connections (Jakob)
# ==============================================================================
def render_uc7_view_connections():
    st.subheader("UC-7: View Friends/Connections")
    st.write("Select a user to view their followers and following lists.")

    users = run_query("""
        MATCH (u:User)
        RETURN u.userId AS id, u.username AS username
        ORDER BY u.username
        LIMIT 500
    """)

    user_list = [f"{r.data()['username']} ({r.data()['id']})" for r in users]
    user_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in users}

    selected_label = st.selectbox("Select User", user_list, key="uc7_user")

    if selected_label:
        user = user_map[selected_label]
        uid = user['id']
        username = user['username']

        st.write(f"### Connections for: **{username}** (ID: {uid})")

        counts = run_query("""
            MATCH (u:User {userId: $uid})
            OPTIONAL MATCH (u)<-[:FOLLOWS]-(follower)
            WITH u, count(DISTINCT follower) AS followerCount
            OPTIONAL MATCH (u)-[:FOLLOWS]->(following)
            RETURN followerCount, count(DISTINCT following) AS followingCount
        """, {"uid": uid})

        if counts:
            c = counts[0].data()
            col1, col2 = st.columns(2)
            col1.metric("Followers", c['followerCount'])
            col2.metric("Following", c['followingCount'])

        tab1, tab2 = st.tabs(["👥 Followers", "➡️ Following"])

        with tab1:
            followers_query = f"""
// UC-7: View Followers
// Returns all users who follow the selected user

MATCH (u:User {{userId: '{uid}'}})<-[:FOLLOWS]-(f:User)
RETURN
    f.userId AS id,
    f.username AS username,
    f.name AS name,
    f.bio AS bio
ORDER BY f.username
LIMIT 100
"""
            st.write("#### Cypher Query")
            st.code(followers_query, language="cypher")

            if st.button("Run Followers Query", key="uc7_followers_run"):
                rows = run_query("""
                    MATCH (u:User {userId: $uid})<-[:FOLLOWS]-(f:User)
                    RETURN f.userId AS id, f.username AS username, f.name AS name, f.bio AS bio
                    ORDER BY f.username LIMIT 100
                """, {"uid": uid})

                df = dataframe(rows)

                if df.empty:
                    st.info("No followers found.")
                else:
                    st.dataframe(df, use_container_width=True)
                    if st.checkbox("Show Graph", key="uc7_followers_graph"):
                        path = graph_from_rows(rows)
                        with open(path) as f:
                            st.components.v1.html(f.read(), height=500)

        with tab2:
            following_query = f"""
// UC-7: View Following
// Returns all users that the selected user follows

MATCH (u:User {{userId: '{uid}'}})-[:FOLLOWS]->(t:User)
RETURN
    t.userId AS id,
    t.username AS username,
    t.name AS name,
    t.bio AS bio
ORDER BY t.username
LIMIT 100
"""
            st.write("#### Cypher Query")
            st.code(following_query, language="cypher")

            if st.button("Run Following Query", key="uc7_following_run"):
                rows = run_query("""
                    MATCH (u:User {userId: $uid})-[:FOLLOWS]->(t:User)
                    RETURN t.userId AS id, t.username AS username, t.name AS name, t.bio AS bio
                    ORDER BY t.username LIMIT 100
                """, {"uid": uid})

                df = dataframe(rows)

                if df.empty:
                    st.info("Not following anyone.")
                else:
                    st.dataframe(df, use_container_width=True)
                    if st.checkbox("Show Graph", key="uc7_following_graph"):
                        path = graph_from_rows(rows)
                        with open(path) as f:
                            st.components.v1.html(f.read(), height=500)


# ==============================================================================
# UC-8: Mutual Connections (Jakob)
# ==============================================================================
def render_uc8_mutual_connections():
    st.subheader("UC-8: Mutual Connections")
    st.write("Find users that **both** User A and User B follow (mutual friends).")

    users = run_query("""
        MATCH (u:User)
        RETURN u.userId AS id, u.username AS username
        ORDER BY u.username
        LIMIT 500
    """)

    user_list = [f"{r.data()['username']} ({r.data()['id']})" for r in users]
    user_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in users}

    col1, col2 = st.columns(2)

    with col1:
        user_a_label = st.selectbox("User A", user_list, key="uc8_user_a")

    with col2:
        user_b_label = st.selectbox("User B", user_list, key="uc8_user_b")

    if user_a_label and user_b_label:
        user_a = user_map[user_a_label]
        user_b = user_map[user_b_label]

        cypher_query = f"""
// UC-8: Mutual Connections
// Finds users that BOTH User A and User B follow

MATCH (a:User {{userId: '{user_a['id']}'}})-[:FOLLOWS]->(mutual:User)<-[:FOLLOWS]-(b:User {{userId: '{user_b['id']}'}})
WHERE a <> b
RETURN DISTINCT
    mutual.userId AS id,
    mutual.username AS username,
    mutual.name AS name,
    mutual.bio AS bio
ORDER BY mutual.username
LIMIT 50
"""

        st.write("### Cypher Query")
        st.code(cypher_query, language="cypher")

        if st.button("Find Mutual Connections", key="uc8_execute"):
            if user_a['id'] == user_b['id']:
                st.warning("Please select two different users!")
            else:
                rows = run_query("""
                    MATCH (a:User {userId: $aid})-[:FOLLOWS]->(mutual:User)<-[:FOLLOWS]-(b:User {userId: $bid})
                    WHERE a <> b
                    RETURN DISTINCT
                        mutual.userId AS id, mutual.username AS username,
                        mutual.name AS name, mutual.bio AS bio
                    ORDER BY mutual.username LIMIT 50
                """, {"aid": user_a['id'], "bid": user_b['id']})

                df = dataframe(rows)

                st.write(f"### Results: {len(df)} mutual connection(s)")

                if df.empty:
                    st.info("No mutual connections found.")
                else:
                    tab1, tab2 = st.tabs(["📊 Table", "🔗 Graph"])

                    with tab1:
                        st.dataframe(df, use_container_width=True)

                    with tab2:
                        path = mutual_graph(rows, user_a, user_b)
                        with open(path) as f:
                            st.components.v1.html(f.read(), height=600)
                        st.caption("🔴 User A | 🟢 User B | 🔵 Mutual Connections")


# ==============================================================================
# UC-9: Friend Recommendations (Jakob)
# ==============================================================================
def render_uc9_friend_recommendations():
    st.subheader("UC-9: Friend Recommendations")
    st.write("Suggest new users to follow based on **friends-of-friends** (2-hop graph traversal).")

    users = run_query("""
        MATCH (u:User)
        RETURN u.userId AS id, u.username AS username
        ORDER BY u.username
        LIMIT 500
    """)

    user_list = [f"{r.data()['username']} ({r.data()['id']})" for r in users]
    user_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in users}

    selected_label = st.selectbox("Select User", user_list, key="uc9_user")
    limit = st.slider("Number of Recommendations", 5, 50, 10, key="uc9_limit")

    if selected_label:
        user = user_map[selected_label]
        uid = user['id']
        username = user['username']

        cypher_query = f"""
// UC-9: Friend Recommendations
// Uses 2-hop graph traversal to find friends-of-friends
// Ranks by number of mutual connections

MATCH (u:User {{userId: '{uid}'}})-[:FOLLOWS]->(friend)-[:FOLLOWS]->(recommended)
WHERE NOT (u)-[:FOLLOWS]->(recommended)
  AND u <> recommended
WITH recommended, count(DISTINCT friend) AS mutualCount
RETURN
    recommended.userId AS id,
    recommended.username AS username,
    recommended.name AS name,
    recommended.bio AS bio,
    mutualCount
ORDER BY mutualCount DESC, recommended.username
LIMIT {limit}
"""

        st.write("### Cypher Query")
        st.code(cypher_query, language="cypher")

        if st.button("Get Recommendations", key="uc9_execute"):
            rows = run_query("""
                MATCH (u:User {userId: $uid})-[:FOLLOWS]->(friend)-[:FOLLOWS]->(recommended)
                WHERE NOT (u)-[:FOLLOWS]->(recommended) AND u <> recommended
                WITH recommended, count(DISTINCT friend) AS mutualCount
                RETURN
                    recommended.userId AS id, recommended.username AS username,
                    recommended.name AS name, recommended.bio AS bio, mutualCount
                ORDER BY mutualCount DESC, recommended.username
                LIMIT $limit
            """, {"uid": uid, "limit": limit})

            df = dataframe(rows)

            st.write(f"### Recommendations for: **{username}**")

            if df.empty:
                st.info("No recommendations found. Try following more users first!")
            else:
                st.write(f"Found {len(df)} recommendation(s)")

                tab1, tab2 = st.tabs(["📊 Table", "🔗 Graph"])

                with tab1:
                    st.dataframe(df, use_container_width=True)

                with tab2:
                    path = recommendation_graph(rows, user)
                    with open(path) as f:
                        st.components.v1.html(f.read(), height=600)
                    st.caption("🔴 You | 🟡 Recommended Users (size = mutual connections)")
