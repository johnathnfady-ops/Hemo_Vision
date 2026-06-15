"""
init_db.py - Initialize Database
Creates database tables and demo user
"""
from app import app, db, User

print("🔧 Initializing database...")

with app.app_context():
    # Create all tables
    db.create_all()
    print("✅ Database tables created")
    
    # Check if demo user exists
    demo_user = User.query.filter_by(email="demo@hemovision.com").first()
    
    if not demo_user:
        # Create demo user
        demo_user = User(
            email="demo@hemovision.com",
            name="Demo User",
            age=30,
            gender="Male",
            blood_type="A+"
        )
        demo_user.set_password("demo123")
        db.session.add(demo_user)
        db.session.commit()
        print("✅ Demo user created")
        print("   Email: demo@hemovision.com")
        print("   Password: demo123")
    else:
        print("ℹ️  Demo user already exists")

print("\n✅ Database initialization complete!")
print("🚀 You can now run: python app.py")
