#!/usr/bin/env python3
"""One-off seed: writes data/products.json from the listings captured from the live Etsy shop
(PrintFluentShop, 60 active listings, Nov 2026). After this, scripts/sync_etsy.py keeps it fresh."""
import json, re, pathlib

# category codes: T tumbler, P planner, S tshirt, R teacher resource, B birthday card
ROWS = """
4548434826|T|2.99|3D Crystal Snowflake Tumbler Wrap, Silver Winter Design (Digital Download)
1858504944|P|1.00|Study Planner | Printable Weekly Study Schedule | Student Organizer | Digital Download
1858553110|P|2.00|Monthly Goal Planner | Productivity & Time Management | Printable PDF
1872768051|P|2.50|Travel Itinerary Planner | Printable Trip Organizer | Vacation Planner PDF
4551687474|T|1.99|Dark Romantic Floral Tumbler Wrap, Red Roses Sublimation Design (Digital Download)
4538422479|T|1.99|3D Pink Bow Teacher Tumbler Wrap, "Teacher Ever" Sublimation PNG (Digital Download)
4538380413|T|1.99|Floral Teacher Tumbler Wrap, Pink White Flowers, Blue Pearl Background (Digital Download)
4537793513|T|2.99|3D Crystal Butterfly Bow Tumbler Wrap, Pink Glam Sublimation PNG (Digital Download)
4536694194|T|1.99|Teacher Tumbler Wrap, Back to School PNG, Apple 20oz Sublimation Design
4536643956|T|1.99|Sunflower Cow Print Tumbler Wrap, Farmhouse Rustic Sublimation Design (Digital Download)
4536363884|T|1.99|Bloom Botanical Tumbler Wrap PNG, Floral Affirmation 20oz Skinny Sublimation Design
4536331499|T|1.99|Soccer Tumbler Wrap PNG, World Cup Sports Sublimation Design (Digital Download)
4536132145|T|1.99|Dark Butterfly Maximalist Tumbler Wrap, Tropical Floral PNG (Digital Download)
4536124657|T|1.99|Blush Pink Watercolor Butterfly Floral Tumbler Wrap (Digital Download)
4536079329|T|1.99|Purple Lavender Butterfly Tumbler Wrap, 20oz Skinny Sublimation PNG (Digital Download)
4535862445|T|1.99|Wildflower Meadow Tumbler Wrap, Watercolor Floral PNG (Digital Download)
4535804007|T|1.99|Boho Celestial Sun Moon Tumbler Wrap, 20oz Skinny Sublimation PNG (Digital Download)
4535773475|T|1.99|Autumn Botanical Tumbler Wrap PNG, Fall Floral Design (Digital Download)
4557544473|T|1.99|Bold Red Heart Tumbler Wrap, Doodle Glitter Valentine Sublimation Design (Digital Download)
4585132810|B|3.49|40th Happy Birthday Card for Her, Botanical Greenhouse Printable Card, Elegant Instant Download
4584455235|B|3.49|30th Birthday Card for Her Printable, Celestial Crystal 30 Card, Elegant Milestone Birthday, Instant Download
4549146763|T|1.99|3D Coquette Bow Tumbler Wrap, Pink Satin Bows Pearls Hearts (Digital Download)
4571460151|B|2.99|Birthday Card for Her Printable, Cottage Garden Floral Card, Elegant Female Birthday Card, Instant Digital Download 5x7
4570163361|S|2.99|Samurai T-Shirt PNG, Japanese Warrior Helmet, Quiet Mind Unbreakable Will Sublimation Design
4569082240|P|2.99|Kawaii Kids Birthday Planner | Fillable PDF Party Checklist, Budget, Guest List (Digital Download)
4569069626|P|2.99|Mom's Birthday Planner - Digital Printable Planner | Budget Tracker, Guest List, Checklist
4568232471|P|2.99|Dad's Birthday Planner - Digital Printable Planner | Budget Tracker, Guest List, Checklist
4567453227|S|1.99|Funny Pet Lover Shirt Design, Paw Print, Dog Mom Cat Mom (Digital Download)
4567475558|S|1.99|Joy Wears Bright Colors Floral Shirt Design, Retro Rainbow Sublimation (Digital Download)
4567448007|S|1.99|Nurse Shirt PNG, Steady Hands Sparkling Soul, Floral Stethoscope Design (Digital Download)
4567446167|S|1.99|Pickleball PNG, Colorful Paddle Shirt Design, Retro Sports Sublimation Download, Pickleball Gift Digital File
4567443331|S|1.99|Retro Fall Pumpkin Shirt Design, Jewel-Tone Autumn Leaves, Sparkle Effect (Digital Download)
4542196060|T|2.99|Samurai Tumbler Wrap PNG, Dark Japanese Ink Art, 20oz Skinny Sublimation Design
4566117811|P|4.99|Birthday Planner - Digital Printable Planner | Budget Tracker, Guest List, Checklist | Instant Download
4566100712|S|1.99|Sunflower Butterfly Leopard Print T-Shirt Design (Digital File)
4566098954|S|1.99|Tiny Wins Big Sparkle T-Shirt Design, Disco Star Bow, Motivational Sublimation (PNG)
4566096014|S|1.99|Teaching in Full Color T-Shirt Design, Retro Teacher Shirt (PNG File)
4566071269|S|1.99|Book Lover Ghost T-Shirt Design, Bright Unbothered PNG (Digital Download)
4566067461|S|1.99|Sunflower Butterfly T-Shirt Design, Bloom Loud Shine Brighter (Digital Download)
4563146466|S|1.99|Retro Camera Shirt Design, Photography Adventure Graphic, Wildflower Sublimation, Transparent Download
4562556433|S|1.99|Retro Teacher Shirt Design, Teach Love Inspire, Colorful Classroom Graphic (Digital Download)
4562575294|S|1.99|Bookish Ghost PNG, Reader Shirt Graphic, Librarian Teacher Sublimation (Digital Download)
4561810183|S|1.99|Salty Air Sunny Hair T-Shirt Design, Retro Tropical Sunset (Digital Download)
4561801071|S|1.99|New and Moms To-be T-shirt, Retro Leopard Print Design (Digital Download)
4560172210|S|0.99|Pet Lover Heart Paw Print Shirt Design, Sentimental Quote (Digital Download)
4558920754|T|1.99|Dad Mode Activated Tumbler Wrap, Industrial Metal Badge Design (Digital File)
4558206434|T|1.99|Kawaii Nurse Tumbler Wrap PNG, Medical Sublimation Design (20oz Skinny Tumbler)
4551132203|T|1.99|3D Floral Butterfly Tumbler Wrap, Pastel Lavender Flowers, Sublimation Design (Digital Download)
4550494018|T|2.99|3D Metallic Hearts Tumbler Wrap, Valentine Sublimation Design (Digital Download)
4549832905|T|2.99|Kawaii Teacher Tumbler Wrap, Teaching Superpower Design (Digital Download)
4549178165|T|2.99|3D Puffy Tumbler Wrap, Kawaii School Supplies Design, Back to School PNG (Digital Download)
4547018620|T|2.99|3D Puffy Heart Tumbler Wrap, Rose Gold Pink Valentine Sublimation Design (Digital Download)
4545751849|R|5.99|Kawaii Y2K First Day School Sign, All About Me, Interview Sheet, Growth Chart (PDF)
4543394437|R|1.99|First Day of School Sign, Chalkboard Photo Prop (PDF Download)
4542266938|T|1.99|Back to School Tumbler Wrap PNG, Stay Curious Classroom 20oz Sublimation Design
4541603894|T|1.99|Teacher Tumbler Wrap PNG, Back to School Classroom 20oz Sublimation Design
4537912638|T|1.99|3D Pink Floral Butterfly Tumbler Wrap, Daisy Pearl Sublimation PNG (Digital Download)
4540484924|T|1.99|3D Red Roses Hearts Tumbler Wrap, Romantic Valentine Sublimation PNG (Digital Download)
4540294569|T|1.99|Teacher Tumbler Wrap, Little Minds Big Hearts Sublimation PNG (Instant Download)
4540068101|P|9.99|Wedding Planner Spreadsheet, Budget, Guest List, Timeline (Digital Download)
""".strip().splitlines()

CATS = {
    "T": "tumbler-wraps",
    "P": "planners-trackers",
    "S": "t-shirt-designs",
    "R": "teacher-resources",
    "B": "birthday-cards",
}
FEATURED = {"4542196060", "4584455235", "4550494018", "4540068101", "4569082240", "4567475558"}


def slugify(t):
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t.lower()).strip("-")
    return "-".join(t.split("-")[:8])


products = []
for i, row in enumerate(ROWS):
    pid, c, price, title = row.split("|", 3)
    products.append({
        "id": pid,
        "slug": slugify(title) + "-" + pid[-4:],
        "title": title,
        "price": float(price),
        "category": CATS[c],
        "etsy_url": f"https://www.etsy.com/listing/{pid}",
        "image": "",          # filled by scripts/sync_etsy.py
        "featured": pid in FEATURED,
        "order": i,           # 0 = newest on the shop
    })

out = pathlib.Path(__file__).resolve().parent.parent / "data" / "products.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({"shop": "PrintFluentShop", "count": len(products), "products": products}, indent=2))
print("wrote", out, len(products), "products")
