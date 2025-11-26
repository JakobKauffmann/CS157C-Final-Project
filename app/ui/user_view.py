import streamlit as st
from db.neo4j_client import run_query
from graph.graph_render import graph_from_rows, mutual_graph, recommendation_graph
from ui.components import dataframe


def render_user_view(user):
    """
    Render the user profile view with full user management and social graph features.
    Implements UC-3, UC-4, UC-5, UC-6, UC-7, UC-8, UC-9 for logged-in users.
    
    Args:
        user: Dictionary containing user info (id, username, name, bio, email)
    """
    # Profile Header
    st.header(f"👤 {user['username']}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Bio:** {user['bio']}")
        st.write(f"**Email:** {user.get('email', 'N/A')}")
    
    with col2:
        # Get follower/following counts
        counts = run_query("""
            MATCH (u:User {userId: $id})
            RETURN 
                SIZE([(u)-[:FOLLOWS]->(t) | t]) AS following,
                SIZE([(f)-[:FOLLOWS]->(u) | f]) AS followers
        """, {"id": user["id"]})[0].data()
        
        st.metric("Followers", counts['followers'])
        st.metric("Following", counts['following'])
    
    st.divider()

    # Main tabs for all features
    tabs = st.tabs([
        "📋 My Profile",
        "✏️ Edit Profile",
        "👥 My Connections", 
        "➕ Follow Users", 
        "🤝 Mutual Friends", 
        "💡 Recommendations"
    ])

    # ==========================================================================
    # Tab 1: View Profile (UC-3)
    # ==========================================================================
    with tabs[0]:
        render_view_profile(user)

    # ==========================================================================
    # Tab 2: Edit Profile (UC-4)
    # ==========================================================================
    with tabs[1]:
        render_edit_profile(user)

    # ==========================================================================
    # Tab 3: My Connections (UC-7)
    # ==========================================================================
    with tabs[2]:
        render_my_connections(user)

    # ==========================================================================
    # Tab 4: Follow/Unfollow Users (UC-5 & UC-6)
    # ==========================================================================
    with tabs[3]:
        render_follow_unfollow(user)

    # ==========================================================================
    # Tab 5: Mutual Friends (UC-8)
    # ==========================================================================
    with tabs[4]:
        render_mutual_friends(user)

    # ==========================================================================
    # Tab 6: Friend Recommendations (UC-9)
    # ==========================================================================
    with tabs[5]:
        render_recommendations(user)


# ==============================================================================
# UC-3: View Profile
# ==============================================================================
def render_view_profile(user):
    st.subheader("📋 My Profile")
    st.write("View your complete profile information and statistics.")
    
    # Fetch fresh profile data with stats
    result = run_query("""
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
    """, {"uid": user["id"]})
    
    if result:
        profile = result[0].data()
        
        st.write("### Account Information")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.write(f"🆔 **User ID:** `{profile['id']}`")
            st.write(f"👤 **Username:** {profile['username']}")
            st.write(f"📧 **Email:** {profile['email']}")
        
        with info_col2:
            st.write(f"📝 **Display Name:** {profile['name']}")
            st.write(f"💬 **Bio:** {profile['bio']}")
        
        st.write("### Social Statistics")
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        with stat_col1:
            st.metric("👥 Followers", profile['followerCount'])
        
        with stat_col2:
            st.metric("➡️ Following", profile['followingCount'])
        
        with stat_col3:
            # Calculate engagement ratio
            if profile['followingCount'] > 0:
                ratio = profile['followerCount'] / profile['followingCount']
                st.metric("📊 F/F Ratio", f"{ratio:.2f}")
            else:
                st.metric("📊 F/F Ratio", "N/A")
        
        # Show recent followers
        st.write("### Recent Followers")
        recent_followers = run_query("""
            MATCH (u:User {userId: $uid})<-[:FOLLOWS]-(f)
            RETURN f.username AS username, f.name AS name
            LIMIT 5
        """, {"uid": user["id"]})
        
        if recent_followers:
            for f in recent_followers:
                data = f.data()
                st.write(f"• **{data['username']}** - {data['name']}")
        else:
            st.info("No followers yet. Share your profile!")


# ==============================================================================
# UC-4: Edit Profile
# ==============================================================================
def render_edit_profile(user):
    st.subheader("✏️ Edit Profile")
    st.write("Update your profile information.")
    
    # Fetch current data
    current = run_query("""
        MATCH (u:User {userId: $uid})
        RETURN u.name AS name, u.email AS email, u.bio AS bio
    """, {"uid": user["id"]})
    
    if current:
        current_data = current[0].data()
        
        st.write("### Update Your Information")
        
        new_name = st.text_input(
            "Display Name", 
            value=current_data['name'], 
            key="edit_name",
            help="Your public display name"
        )
        
        new_email = st.text_input(
            "Email Address", 
            value=current_data['email'], 
            key="edit_email",
            help="Your email address"
        )
        
        new_bio = st.text_area(
            "Bio", 
            value=current_data['bio'], 
            key="edit_bio",
            help="Tell others about yourself",
            height=100
        )
        
        st.write("### Change Password")
        
        col1, col2 = st.columns(2)
        with col1:
            new_password = st.text_input(
                "New Password (leave blank to keep current)", 
                type="password",
                key="edit_password"
            )
        with col2:
            confirm_password = st.text_input(
                "Confirm New Password", 
                type="password",
                key="edit_confirm_password"
            )
        
        st.divider()
        
        col_a, col_b = st.columns([1, 3])
        
        with col_a:
            if st.button("💾 Save Changes", key="save_profile"):
                errors = []
                
                # Validation
                if not new_name:
                    errors.append("Name cannot be empty")
                if not new_email or "@" not in new_email:
                    errors.append("Valid email is required")
                if new_password and len(new_password) < 4:
                    errors.append("Password must be at least 4 characters")
                if new_password and new_password != confirm_password:
                    errors.append("Passwords do not match")
                
                # Check email uniqueness
                if new_email != current_data['email']:
                    existing = run_query("""
                        MATCH (u:User {email: $email})
                        WHERE u.userId <> $uid
                        RETURN u.email
                    """, {"email": new_email, "uid": user["id"]})
                    
                    if existing:
                        errors.append(f"Email '{new_email}' is already in use")
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                else:
                    # Update profile
                    if new_password:
                        import bcrypt
                        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                        run_query("""
                            MATCH (u:User {userId: $uid})
                            SET u.name = $name,
                                u.email = $email,
                                u.bio = $bio,
                                u.passwordHash = $passwordHash
                        """, {
                            "uid": user["id"],
                            "name": new_name,
                            "email": new_email,
                            "bio": new_bio,
                            "passwordHash": password_hash
                        })
                    else:
                        run_query("""
                            MATCH (u:User {userId: $uid})
                            SET u.name = $name,
                                u.email = $email,
                                u.bio = $bio
                        """, {
                            "uid": user["id"],
                            "name": new_name,
                            "email": new_email,
                            "bio": new_bio
                        })
                    
                    # Update session state
                    st.session_state.logged_in_user['name'] = new_name
                    st.session_state.logged_in_user['email'] = new_email
                    st.session_state.logged_in_user['bio'] = new_bio
                    
                    st.success("✅ Profile updated successfully!")
                    st.rerun()


# ==============================================================================
# UC-7: My Connections (Followers & Following)
# ==============================================================================
def render_my_connections(user):
    st.subheader("👥 My Connections")
    st.write("View who follows you and who you follow.")
    
    sub_tabs = st.tabs(["👥 Followers", "➡️ Following"])
    
    # --- Followers ---
    with sub_tabs[0]:
        st.write("**People who follow you:**")
        
        rows = run_query("""
            MATCH (u:User {userId: $id})<-[:FOLLOWS]-(f)
            RETURN f.userId AS id, f.username AS username, f.name AS name, f.bio AS bio
            ORDER BY f.username
            LIMIT 100
        """, {"id": user["id"]})
        
        df = dataframe(rows)
        
        if df.empty:
            st.info("No followers yet. Share your profile to get followers!")
        else:
            st.write(f"**{len(df)} follower(s)**")
            st.dataframe(df, use_container_width=True)
            
            if st.checkbox("Show Followers Graph", key="user_view_followers_graph"):
                path = graph_from_rows(rows)
                with open(path) as f:
                    st.components.v1.html(f.read(), height=500)

    # --- Following ---
    with sub_tabs[1]:
        st.write("**People you follow:**")
        
        rows = run_query("""
            MATCH (u:User {userId: $id})-[:FOLLOWS]->(t)
            RETURN t.userId AS id, t.username AS username, t.name AS name, t.bio AS bio
            ORDER BY t.username
            LIMIT 100
        """, {"id": user["id"]})
        
        df = dataframe(rows)
        
        if df.empty:
            st.info("You're not following anyone yet. Check out the Recommendations tab!")
        else:
            st.write(f"**Following {len(df)} user(s)**")
            st.dataframe(df, use_container_width=True)
            
            if st.checkbox("Show Following Graph", key="user_view_following_graph"):
                path = graph_from_rows(rows)
                with open(path) as f:
                    st.components.v1.html(f.read(), height=500)


# ==============================================================================
# UC-5 & UC-6: Follow / Unfollow Users
# ==============================================================================
def render_follow_unfollow(user):
    st.subheader("➕ Follow / Unfollow Users")
    
    sub_tabs = st.tabs(["➕ Follow Someone", "➖ Unfollow Someone"])
    
    # --- Follow Someone (UC-5) ---
    with sub_tabs[0]:
        st.write("Search for a user to follow:")
        
        search_term = st.text_input("Search by username or name", key="follow_search")
        
        if search_term:
            # Search for users (excluding self and already-followed)
            results = run_query("""
                MATCH (target:User)
                WHERE (toLower(target.username) CONTAINS toLower($q)
                   OR toLower(target.name) CONTAINS toLower($q))
                  AND target.userId <> $myId
                  AND NOT EXISTS {
                      MATCH (me:User {userId: $myId})-[:FOLLOWS]->(target)
                  }
                RETURN target.userId AS id, target.username AS username, 
                       target.name AS name, target.bio AS bio
                ORDER BY target.username
                LIMIT 20
            """, {"q": search_term, "myId": user["id"]})
            
            if not results:
                st.info("No users found (or you already follow all matching users).")
            else:
                st.write(f"**Found {len(results)} user(s) you can follow:**")
                
                for r in results:
                    data = r.data()
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{data['username']}** - {data['name']}")
                        bio_preview = data['bio'][:50] + "..." if len(data['bio']) > 50 else data['bio']
                        st.caption(bio_preview)
                    
                    with col2:
                        if st.button("Follow", key=f"follow_{data['id']}"):
                            run_query("""
                                MATCH (me:User {userId: $myId})
                                MATCH (target:User {userId: $targetId})
                                MERGE (me)-[:FOLLOWS]->(target)
                            """, {"myId": user["id"], "targetId": data["id"]})
                            st.success(f"✅ You now follow {data['username']}!")
                            st.rerun()
                    
                    st.divider()

    # --- Unfollow Someone (UC-6) ---
    with sub_tabs[1]:
        st.write("Select a user to unfollow:")
        
        # Get current following list
        following = run_query("""
            MATCH (u:User {userId: $id})-[:FOLLOWS]->(t)
            RETURN t.userId AS id, t.username AS username, t.name AS name
            ORDER BY t.username
        """, {"id": user["id"]})
        
        if not following:
            st.info("You're not following anyone yet.")
        else:
            following_list = [f"{r.data()['username']} ({r.data()['id']})" for r in following]
            following_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in following}
            
            selected = st.selectbox("Select user to unfollow", following_list, key="unfollow_select")
            
            if selected:
                target = following_map[selected]
                
                st.warning(f"Are you sure you want to unfollow **{target['username']}**?")
                
                if st.button("🚫 Unfollow", key="confirm_unfollow"):
                    run_query("""
                        MATCH (me:User {userId: $myId})-[r:FOLLOWS]->(target:User {userId: $targetId})
                        DELETE r
                    """, {"myId": user["id"], "targetId": target["id"]})
                    st.success(f"✅ You unfollowed {target['username']}")
                    st.rerun()


# ==============================================================================
# UC-8: Mutual Friends
# ==============================================================================
def render_mutual_friends(user):
    st.subheader("🤝 Mutual Friends")
    st.write("Find users that both you and another user follow.")
    
    # Get users you follow for the dropdown
    following = run_query("""
        MATCH (u:User {userId: $id})-[:FOLLOWS]->(t)
        RETURN t.userId AS id, t.username AS username
        ORDER BY t.username
    """, {"id": user["id"]})
    
    if not following:
        st.info("You need to follow some users first to find mutual friends.")
        return
    
    following_list = [f"{r.data()['username']} ({r.data()['id']})" for r in following]
    following_map = {f"{r.data()['username']} ({r.data()['id']})": r.data() for r in following}
    
    selected = st.selectbox(
        "Select a user to find mutual friends with", 
        following_list, 
        key="mutual_select"
    )
    
    if selected and st.button("Find Mutual Friends", key="find_mutual"):
        other_user = following_map[selected]
        
        # Find users both follow
        rows = run_query("""
            MATCH (me:User {userId: $myId})-[:FOLLOWS]->(mutual:User)<-[:FOLLOWS]-(other:User {userId: $otherId})
            RETURN DISTINCT
                mutual.userId AS id,
                mutual.username AS username,
                mutual.name AS name,
                mutual.bio AS bio
            ORDER BY mutual.username
            LIMIT 50
        """, {"myId": user["id"], "otherId": other_user["id"]})
        
        df = dataframe(rows)
        
        st.write(f"### Mutual friends with {other_user['username']}: {len(df)}")
        
        if df.empty:
            st.info(f"You and {other_user['username']} don't follow any of the same users.")
        else:
            tab1, tab2 = st.tabs(["📊 List", "🔗 Graph"])
            
            with tab1:
                st.dataframe(df, use_container_width=True)
            
            with tab2:
                me_data = {"id": user["id"], "username": user["username"]}
                path = mutual_graph(rows, me_data, other_user)
                with open(path) as f:
                    st.components.v1.html(f.read(), height=500)
                st.caption("🔴 You | 🟢 Other User | 🔵 Mutual Friends")


# ==============================================================================
# UC-9: Friend Recommendations
# ==============================================================================
def render_recommendations(user):
    st.subheader("💡 Friend Recommendations")
    st.write("People you might want to follow based on your connections.")
    
    limit = st.slider("Number of recommendations", 5, 30, 10, key="rec_limit")
    
    if st.button("🔍 Get Recommendations", key="get_recs"):
        rows = run_query("""
            MATCH (me:User {userId: $myId})-[:FOLLOWS]->(friend)-[:FOLLOWS]->(recommended)
            WHERE NOT (me)-[:FOLLOWS]->(recommended)
              AND me <> recommended
            WITH recommended, count(DISTINCT friend) AS mutualCount
            RETURN 
                recommended.userId AS id,
                recommended.username AS username,
                recommended.name AS name,
                recommended.bio AS bio,
                mutualCount
            ORDER BY mutualCount DESC, recommended.username
            LIMIT $limit
        """, {"myId": user["id"], "limit": limit})
        
        df = dataframe(rows)
        
        if df.empty:
            st.info("No recommendations yet. Try following more users first!")
        else:
            st.write(f"**Found {len(df)} recommendations:**")
            
            tab1, tab2 = st.tabs(["📋 List", "🔗 Graph"])
            
            with tab1:
                for r in rows:
                    data = r.data()
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{data['username']}** - {data['name']}")
                        st.caption(f"{data['mutualCount']} mutual connection(s)")
                    
                    with col2:
                        st.write(f"🤝 {data['mutualCount']}")
                    
                    with col3:
                        if st.button("Follow", key=f"rec_follow_{data['id']}"):
                            run_query("""
                                MATCH (me:User {userId: $myId})
                                MATCH (target:User {userId: $targetId})
                                MERGE (me)-[:FOLLOWS]->(target)
                            """, {"myId": user["id"], "targetId": data["id"]})
                            st.success(f"✅ You now follow {data['username']}!")
                            st.rerun()
                    
                    st.divider()
            
            with tab2:
                me_data = {"id": user["id"], "username": user["username"]}
                path = recommendation_graph(rows, me_data)
                with open(path) as f:
                    st.components.v1.html(f.read(), height=500)
                st.caption("🔴 You | 🟡 Recommended (size = mutual count)")
