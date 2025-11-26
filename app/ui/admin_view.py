import streamlit as st
from ui.components import two_panel_query_ui, dataframe
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
    # TODO: UC-7: View User Connections -> THIS HAS BUGS
    # ======================================================
    st.subheader("UC-7: View User Connections")
    st.write("Select a user to view their followers and following lists.")

    # Load all users for dropdown
    users = run_query("""
        MATCH (u:User)
        RETURN u.userId AS id, u.username AS username
        ORDER BY username
    """)

    user_map = {
        f"{row['username']} ({row['id']})": row["id"]
        for row in (r.data() for r in users)
    }
    selected_label = st.selectbox("Select User", list(user_map.keys()))

    # Placeholder template queries shown to admin
    default_followers_query = """
    MATCH (u:User {userId: '<SELECT_USER_ID>', username: '<SELECT_USERNAME>'})<-[:FOLLOWS]-(f)
    RETURN 
        f.userId AS id,
        f.username AS username,
        f.name AS name,
        f.bio AS bio
    ORDER BY username
    """

    default_following_query = """
    MATCH (u:User {userId: '<SELECT_USER_ID>', username: '<SELECT_USERNAME>'})-[:FOLLOWS]->(t)
    RETURN 
        t.userId AS id,
        t.username AS username,
        t.name AS name,
        t.bio AS bio
    ORDER BY username
    """

    if selected_label:
        uid = user_map[selected_label]

        # Extract username from "Username (ID)"
        username = selected_label.split(" (")[0]

        st.write(f"### Viewing Connections for: **{username} ({uid})**")
        st.divider()

        # Followers
        rendered_followers_query = default_followers_query.replace(
            "<SELECT_USER_ID>", str(uid)
        ).replace("<SELECT_USERNAME>", username)

        two_panel_query_ui(
            f"UC-7 Followers of {username} ({uid})", rendered_followers_query
        )

        st.divider()

        # Following
        rendered_following_query = default_following_query.replace(
            "<SELECT_USER_ID>", str(uid)
        ).replace("<SELECT_USERNAME>", username)

        two_panel_query_ui(
            f"UC-7 Following of {username} ({uid})", rendered_following_query
        )

        st.divider()

    # ======================================================
    # UC-8 and UC-9 placeholders
    # ======================================================
    for i in range(8, 10):
        st.subheader(f"UC-{i}: Placeholder")
        st.info("Team member implementation here.")
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
