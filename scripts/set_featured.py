#!/usr/bin/env python3
"""Set featured: true on selected listings by slug."""
import json, glob

FEATURE_SLUGS = {
    'angeldown-legal-video-services-atlanta',   # Atlanta
    'bishop-legal-video-austin',                # Austin
    'action-video-productions-inc-miami',       # Miami
    'coash-court-reporting-video-phoenix',      # Phoenix
    'engen-court-reporting-and-video-service-minneapolis',  # Minneapolis
}

updated = 0
for f in sorted(glob.glob('/Users/nick/Desktop/depohire-src/src/data/listings/*.json')):
    listings = json.load(open(f))
    changed = False
    for l in listings:
        if l.get('slug') in FEATURE_SLUGS:
            l['featured'] = True
            print(f"  featured: {l['name']} ({l.get('city')}) — {l.get('email')}")
            updated += 1
            changed = True
    if changed:
        with open(f, 'w') as out:
            json.dump(listings, out, indent=2)

print(f"\nTotal featured: {updated}")
