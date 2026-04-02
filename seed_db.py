"""
seed_db.py — Populate the database with sample products.
Run once:  python seed_db.py
"""
import shutil, os
from app import create_app
from models import db, Product

# Generated product images (map filename -> source path in artifacts)
# After running, images will be in static/images/products/
SAMPLE_PRODUCTS = [
    # ── TMT Bars ──────────────────────────────────────────────────────────
    {
        "name": "FORGE-06 REBAR", "slug": "forge-06-rebar",
        "description": "Light-gauge TMT bar ideal for binding and secondary reinforcement in slabs, footings, and minor concrete works.",
        "price": 28000, "diameter": "6.0 mm", "length": "12.0 Meters", "weight": "~2.7 Kg",
        "grade": "Grade 40", "compliance": "ASTM A615", "category": "tmt_bars",
        "image": "forge_06.jpg", "in_stock": True, "featured": False, "badge": "IN STOCK",
    },
    {
        "name": "FORGE-08 STIRRUP", "slug": "forge-08-stirrup",
        "description": "Precision engineered for column stirrups and secondary reinforcement. High flexibility for complex shaping in tight radius bends.",
        "price": 43250, "diameter": "8.0 mm", "length": "12.0 Meters", "weight": "~4.7 Kg",
        "grade": "Grade 40", "compliance": "ASTM A615", "category": "tmt_bars",
        "image": "forge_08.jpg", "in_stock": True, "featured": False, "badge": "IN STOCK",
    },
    {
        "name": "FORGE-10 REBAR", "slug": "forge-10-rebar",
        "description": "Versatile structural rod for slabs, walkways, and stair casing. Balanced weight-to-strength ratio for light construction.",
        "price": 99000, "diameter": "10.0 mm", "length": "12.0 Meters", "weight": "~7.4 Kg",
        "grade": "Grade 60", "compliance": "ASTM A615", "category": "tmt_bars",
        "image": "forge_10.jpg", "in_stock": True, "featured": False, "badge": "IN STOCK",
    },
    {
        "name": "FORGE-12 REBAR", "slug": "forge-12-rebar",
        "description": "Optimised for medium-load residential structures. Superior rib pattern for concrete bonding. High tensile strength with excellent workability.",
        "price": 84000, "diameter": "12.0 mm", "length": "12.0 Meters", "weight": "~10.6 Kg",
        "grade": "Grade 60", "compliance": "ASTM A615", "category": "tmt_bars",
        "image": "forge_12.jpg", "in_stock": True, "featured": True, "badge": "IN STOCK",
    },
    {
        "name": "FORGE-16 REBAR", "slug": "forge-16-rebar",
        "description": "Precision commercial grade reinforcement bar. High seismic resistance and excellent formability. Ideal for mid-rise structures.",
        "price": 118000, "diameter": "16.0 mm", "length": "12.0 Meters", "weight": "~18.9 Kg",
        "grade": "Grade 60", "compliance": "ASTM A615", "category": "tmt_bars",
        "image": "forge_16.jpg", "in_stock": True, "featured": True, "badge": "POPULAR",
    },
    {
        "name": "FORGE-20 REBAR", "slug": "forge-20-rebar",
        "description": "Heavy-duty reinforcement for high-rise infrastructure. Maximum yield strength for bridge decks, heavy column work and massive slab pours.",
        "price": 169750, "diameter": "20.0 mm", "length": "12.0 Meters", "weight": "~29.6 Kg",
        "grade": "Grade 75", "compliance": "ASTM A615", "category": "tmt_bars",
        "image": "forge_20.jpg", "in_stock": True, "featured": True, "badge": "POPULAR",
    },
    {
        "name": "FORGE-25 REBAR", "slug": "forge-25-rebar",
        "description": "Industrial-grade for bridge pillars and heavy industrial foundations. Exceptional ductility under seismic loads with superior bond strength.",
        "price": 210000, "diameter": "25.0 mm", "length": "12.0 Meters", "weight": "~46.3 Kg",
        "grade": "Grade 60", "compliance": "ASTM A615", "category": "tmt_bars",
        "image": "forge_25.jpg", "in_stock": True, "featured": True, "badge": "GRADE 60",
    },
    {
        "name": "FORGE-32 REBAR", "slug": "forge-32-rebar",
        "description": "Extra heavy-duty bar for large-scale infrastructure, dam construction, and massive retaining wall systems requiring exceptional tensile strength.",
        "price": 380000, "diameter": "32.0 mm", "length": "12.0 Meters", "weight": "~75.8 Kg",
        "grade": "Grade 75", "compliance": "ASTM A615", "category": "tmt_bars",
        "image": "forge_32.jpg", "in_stock": True, "featured": True, "badge": "HEAVY DUTY",
    },
    {
        "name": "FORGE-40 REBAR", "slug": "forge-40-rebar",
        "description": "Maximum-diameter bar for major civil engineering and infrastructure projects —dams, power stations, and deep foundations.",
        "price": 520000, "diameter": "40.0 mm", "length": "12.0 Meters", "weight": "~118.4 Kg",
        "grade": "Grade 75", "compliance": "ASTM A615", "category": "tmt_bars",
        "image": "forge_40.jpg", "in_stock": False, "featured": False, "badge": "ON DEMAND",
    },

    # ── Round Bars ────────────────────────────────────────────────────────
    {
        "name": "MILD ROUND ROD 8mm", "slug": "mild-round-rod-8mm",
        "description": "Smooth mild steel round bar for general fabrication, gate construction, and light structural work. Easy to bend and weld.",
        "price": 38000, "diameter": "8.0 mm", "length": "6.0 Meters", "weight": "~2.4 Kg",
        "grade": "Grade 250", "compliance": "ASTM A36", "category": "round_bars",
        "image": "mild_8.jpg", "in_stock": True, "featured": False, "badge": "IN STOCK",
    },
    {
        "name": "MILD ROUND ROD 10mm", "slug": "mild-round-rod-10mm",
        "description": "Smooth round bar widely used for dowel bars, door frames, window guards, grille fabrication, and general metalwork.",
        "price": 55000, "diameter": "10.0 mm", "length": "6.0 Meters", "weight": "~3.7 Kg",
        "grade": "Grade 250", "compliance": "ASTM A36", "category": "round_bars",
        "image": "mild_10.jpg", "in_stock": True, "featured": False, "badge": "IN STOCK",
    },
    {
        "name": "DEFORMED BAR 20mm", "slug": "deformed-bar-20mm",
        "description": "High-yield deformed reinforcement bar with superior rib geometry for maximum concrete bond and shear resistance in slabs and beams.",
        "price": 175000, "diameter": "20.0 mm", "length": "12.0 Meters", "weight": "~29.6 Kg",
        "grade": "Grade 60", "compliance": "BS 4449", "category": "round_bars",
        "image": "forge_20.jpg", "in_stock": True, "featured": False, "badge": "GRADE 60",
    },

    # ── Square Bars ───────────────────────────────────────────────────────
    {
        "name": "SQUARE ROD 16mm", "slug": "square-rod-16mm",
        "description": "Medium square cross-section steel bar for staircase railings, grille fabrication, decorative gates, and light structural frames.",
        "price": 95000, "diameter": "16.0 mm", "length": "6.0 Meters", "weight": "~12.0 Kg",
        "grade": "Grade 250", "compliance": "ASTM A36", "category": "square_bars",
        "image": "sq_rod_16.jpg", "in_stock": True, "featured": False, "badge": "IN STOCK",
    },
    {
        "name": "SQUARE ROD 25mm", "slug": "square-rod-25mm",
        "description": "Heavy-duty square bar for staircases, industrial frames, and structural fabrication requiring high strength-to-weight ratio.",
        "price": 135000, "diameter": "25.0 mm", "length": "6.0 Meters", "weight": "~29.5 Kg",
        "grade": "Grade 60", "compliance": "ASTM A36", "category": "square_bars",
        "image": "forge_sq25.jpg", "in_stock": True, "featured": False, "badge": "IN STOCK",
    },
    {
        "name": "FLAT BAR 50x6mm", "slug": "flat-bar-50x6mm",
        "description": "Mild steel flat bar for structural supports, frame brackets, base plates, and general fabrication in construction and manufacturing.",
        "price": 78000, "diameter": "50x6 mm", "length": "6.0 Meters", "weight": "~14.1 Kg",
        "grade": "Grade 250", "compliance": "ASTM A36", "category": "square_bars",
        "image": "flat_bar.jpg", "in_stock": True, "featured": False, "badge": "IN STOCK",
    },

    # ── Accessories & Consumables ─────────────────────────────────────────
    {
        "name": "BINDING WIRE 50KG", "slug": "binding-wire-50kg",
        "description": "Black annealed soft iron binding wire for tying rebar joints in reinforced concrete. Flexible, corrosion-resistant, easy to twist by hand.",
        "price": 32500, "diameter": "1.6 mm", "length": "50 Kg Coil", "weight": "50 Kg",
        "grade": "Soft Annealed", "compliance": "BS 4482", "category": "round_bars",
        "image": "binding_wire.jpg", "in_stock": True, "featured": False, "badge": "IN STOCK",
    },
    {
        "name": "BRC STEEL MESH A393", "slug": "brc-mesh-a393",
        "description": "Pre-welded high-yield fabric reinforcement mesh for suspended floor slabs, ground slabs, retaining walls, and road pavements.",
        "price": 125000, "diameter": "10.0 mm", "length": "6.0 x 2.4 m Sheet", "weight": "~93 Kg",
        "grade": "Grade 460", "compliance": "BS 4483", "category": "round_bars",
        "image": "forge_16.jpg", "in_stock": True, "featured": False, "badge": "POPULAR",
    },
    # ── TMT Bars (Extra) ──────────────────────────────────────────────────
    {
        "name": "FORGE-28 REBAR", "slug": "forge-28-rebar",
        "description": "Custom gauge TMT bar for specific structural requirements in heavy load-bearing residential complexes and parking garages.",
        "price": 245000, "diameter": "28.0 mm", "length": "12.0 Meters", "weight": "~58.5 Kg",
        "grade": "Grade 60", "compliance": "ASTM A615", "category": "tmt_bars",
        "image": "forge_25.jpg", "in_stock": True, "featured": False, "badge": "NEW",
    },
    {
        "name": "FORGE-50 REBAR", "slug": "forge-50-rebar",
        "description": "Ultra heavy-duty structural rod for critical infrastructure like sea walls, deep harbor foundations, and bridge abutments.",
        "price": 680000, "diameter": "50.0 mm", "length": "12.0 Meters", "weight": "~184.8 Kg",
        "grade": "Grade 75+,", "compliance": "ASTM A615", "category": "tmt_bars",
        "image": "forge_40.jpg", "in_stock": False, "featured": False, "badge": "INDUSTRIAL",
    },

    # ── Round Bars (Extra) ────────────────────────────────────────────────
    {
        "name": "MILD FLAT BAR 100x12mm", "slug": "flat-bar-100x12mm",
        "description": "High-strength mild steel flat bar for structural reinforcement, base plates, and heavy machinery mounts. Precision thickness for industrial use.",
        "price": 115000, "diameter": "100x12 mm", "length": "6.0 Meters", "weight": "~56.4 Kg",
        "grade": "Grade 250", "compliance": "ASTM A36", "category": "square_bars",
        "image": "flat_bar.jpg", "in_stock": True, "featured": False, "badge": "IN STOCK",
    },

    # ── Accessories & Consumables (Extra) ─────────────────────────────────
    {
        "name": "STEEL BOLT-16 (100 PK)", "slug": "steel-bolt-16-100pk",
        "description": "High-tensile Grade 8.8 steel bolts for structural steel connections and heavy-duty timber fixing. Includes matching nuts and washers.",
        "price": 45000, "diameter": "16.0 mm", "length": "100mm", "weight": "12 Kg",
        "grade": "Grade 8.8", "compliance": "ISO 898", "category": "round_bars",
        "image": "binding_wire.jpg", "in_stock": True, "featured": False, "badge": "NEW",
    },
    {
        "name": "REBAR CHAIR 25mm (500 PK)", "slug": "rebar-chair-25mm",
        "description": "Heavy-duty plastic rebar spacers for maintaining proper concrete cover in slabs and footings. Designed for 12-25mm rebars.",
        "price": 18500, "diameter": "25.0 mm", "length": "N/A", "weight": "5 Kg",
        "grade": "HDPE", "compliance": "ASTM C127", "category": "round_bars",
        "image": "binding_wire.jpg", "in_stock": True, "featured": False, "badge": "IN STOCK",
    },
]


def seed():
    app = create_app()
    with app.app_context():
        # Ensure tables are created first
        db.create_all()
        
        # Clear existing products
        Product.query.delete()
        db.session.commit()

        # Ensure image folder exists
        os.makedirs('static/images/products', exist_ok=True)

        for data in SAMPLE_PRODUCTS:
            p = Product(**data)
            db.session.add(p)

        db.session.commit()
        print(f"[OK] Seeded {len(SAMPLE_PRODUCTS)} products successfully.")


if __name__ == '__main__':
    seed()
