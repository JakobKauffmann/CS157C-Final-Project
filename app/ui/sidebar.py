import streamlit as st
from db.neo4j_client import run_query
import bcrypt


def render_sidebar():
    """
    Render the sidebar with mode selection, login, and registration functionality.
    Returns the selected mode ('Admin' or 'User').
    """
    st.sidebar.title("Mode")

    mode = st.sidebar.radio("View as", ["Admin", "User"])

    # Initialize session states
    if "logged_in_user" not in st.session_state:
        st.session_state.logged_in_user = None
    if "show_registration" not in st.session_state:
        st.session_state.show_registration = False

    if mode == "User":
        # Show logged in status at top if logged in
        if st.session_state.logged_in_user:
            st.sidebar.success(f"✅ Logged in as: **{st.session_state.logged_in_user['username']}**")
            if st.sidebar.button("Logout", key="sidebar_logout"):
                st.session_state.logged_in_user = None
                st.sidebar.info("Logged out successfully.")
                st.rerun()
        else:
            # Toggle between Login and Register
            auth_mode = st.sidebar.radio(
                "Action", 
                ["Login", "Register New Account"],
                key="auth_mode"
            )
            
            if auth_mode == "Login":
                render_login_form()
            else:
                render_registration_form()

    return mode


def render_login_form():
    """
    Render the login form in the sidebar (UC-2: User Login).
    """
    st.sidebar.subheader("🔐 Login")
    
    username = st.sidebar.text_input("Username", key="login_username")
    password = st.sidebar.text_input("Password", type="password", key="login_password")
    
    if st.sidebar.button("Login", key="login_btn"):
        if not username or not password:
            st.sidebar.error("Please enter username and password")
        else:
            rows = run_query("""
                MATCH (u:User {username: $u})
                RETURN u.userId AS id, u.username AS username, 
                       u.passwordHash AS phash,
                       u.name AS name, u.bio AS bio, u.email AS email
            """, {"u": username})

            if not rows:
                st.sidebar.error("❌ User not found.")
            else:
                data = rows[0].data()
                if bcrypt.checkpw(password.encode(), data["phash"].encode()):
                    # Store user without password hash
                    st.session_state.logged_in_user = {
                        "id": data["id"],
                        "username": data["username"],
                        "name": data["name"],
                        "bio": data["bio"],
                        "email": data["email"]
                    }
                    st.sidebar.success(f"✅ Welcome, {data['name']}!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Invalid password")
    
    st.sidebar.caption("💡 Default password for all users: `password`")


def render_registration_form():
    """
    Render the registration form in the sidebar (UC-1: User Registration).
    """
    st.sidebar.subheader("📝 Register")
    
    new_username = st.sidebar.text_input("Username", key="reg_username", placeholder="Choose a username")
    new_email = st.sidebar.text_input("Email", key="reg_email", placeholder="your@email.com")
    new_name = st.sidebar.text_input("Full Name", key="reg_name", placeholder="Your Name")
    new_bio = st.sidebar.text_input("Bio (optional)", key="reg_bio", placeholder="About you...")
    new_password = st.sidebar.text_input("Password", type="password", key="reg_password")
    confirm_password = st.sidebar.text_input("Confirm Password", type="password", key="reg_confirm")
    
    if st.sidebar.button("Create Account", key="register_btn"):
        # Validation
        errors = []
        
        if not new_username:
            errors.append("Username is required")
        elif len(new_username) < 3:
            errors.append("Username must be at least 3 characters")
            
        if not new_email:
            errors.append("Email is required")
        elif "@" not in new_email:
            errors.append("Invalid email format")
            
        if not new_name:
            errors.append("Name is required")
            
        if not new_password:
            errors.append("Password is required")
        elif len(new_password) < 4:
            errors.append("Password must be at least 4 characters")
        elif new_password != confirm_password:
            errors.append("Passwords do not match")
        
        if errors:
            for error in errors:
                st.sidebar.error(f"❌ {error}")
        else:
            # Check if username exists
            existing = run_query("""
                MATCH (u:User {username: $username})
                RETURN u.username
            """, {"username": new_username})
            
            if existing:
                st.sidebar.error(f"❌ Username '{new_username}' is already taken")
            else:
                # Check if email exists
                existing_email = run_query("""
                    MATCH (u:User {email: $email})
                    RETURN u.email
                """, {"email": new_email})
                
                if existing_email:
                    st.sidebar.error(f"❌ Email '{new_email}' is already registered")
                else:
                    # Generate new user ID
                    max_id_result = run_query("""
                        MATCH (u:User)
                        RETURN max(toInteger(u.userId)) AS maxId
                    """)
                    max_id = max_id_result[0].data()['maxId'] if max_id_result else 0
                    new_id = f"{(max_id or 0) + 1:04d}"
                    
                    # Hash password
                    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                    
                    # Create user
                    result = run_query("""
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
                            u.name AS name,
                            u.bio AS bio,
                            u.email AS email
                    """, {
                        "userId": new_id,
                        "username": new_username,
                        "email": new_email,
                        "name": new_name,
                        "bio": new_bio or f"Hello, I'm {new_name}!",
                        "passwordHash": password_hash
                    })
                    
                    if result:
                        user_data = result[0].data()
                        st.sidebar.success(f"✅ Account created! ID: {new_id}")
                        
                        # Auto-login the new user
                        st.session_state.logged_in_user = user_data
                        st.rerun()
