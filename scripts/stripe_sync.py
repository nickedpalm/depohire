#!/usr/bin/env python3
"""Sync a vertical's Stripe products, prices, and payment links with its yaml config.

Reads `pricing` block from configs/<slug>.yaml, ensures matching Stripe resources
exist (creates if missing, reuses if matched by metadata), and writes the resulting
product/price/payment-link identifiers back into the yaml.

Idempotency: products and prices are matched by metadata {vertical, kind} (kind ∈
{featured, city_pro}). When the monthly/annual USD amount in yaml differs from the
active Stripe price, a new price is created and a new payment link is generated;
the superseded payment link is deactivated (Stripe prices are immutable).

Usage:
    python3 scripts/stripe_sync.py --vertical <slug> [--execute]

Default is dry-run: GETs real state from Stripe to report reuse/create decisions,
but simulates writes. Pass --execute for live writes. Requires STRIPE_SECRET_KEY
in env (sk_live_, sk_test_, or rk_live_/rk_test_).
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
STRIPE_API = "https://api.stripe.com/v1"

TIERS = [
    # (kind, yaml_prefix, display_suffix, statement_descriptor_suffix)
    ("featured", "featured", "Featured Listing", "FEATURED"),
    ("city_pro", "city_pro", "City Pro", "CITYPRO"),
]
INTERVALS = [
    # (interval, yaml_price_field, stripe_recurring_interval)
    ("monthly", "monthly_usd", "month"),
    ("annual", "annual_usd", "year"),
]

PRODUCT_DESCRIPTIONS = {
    "featured": (
        "Pin your listing to the top of {brand} city pages. "
        "Enhanced card, trust badges, priority in search. Includes analytics. "
        "Cancel anytime."
    ),
    "city_pro": (
        "Exclusive city-level sponsorship on {brand}. "
        "Only one provider per city — single-spot dominance of inbound leads "
        "from that city's page. Includes analytics and lead routing."
    ),
}


@dataclass
class PlannedAction:
    verb: str      # "create" | "reuse" | "new-price" | "deactivate-link"
    resource: str  # "product" | "price" | "payment_link"
    kind: str
    interval: str
    detail: str

    def __str__(self) -> str:
        return f"  {self.verb:16s} {self.resource:13s} {self.kind:9s}/{self.interval:7s}  {self.detail}"


@dataclass
class SyncContext:
    vertical: str
    brand: str
    domain: str
    pricing: dict
    planned: list[PlannedAction] = field(default_factory=list)


def load_yaml(slug: str) -> dict:
    path = PROJECT_ROOT / "configs" / f"{slug}.yaml"
    with path.open() as f:
        return yaml.safe_load(f)


def dump_yaml(slug: str, config: dict) -> None:
    path = PROJECT_ROOT / "configs" / f"{slug}.yaml"
    with path.open("w") as f:
        yaml.safe_dump(config, f, sort_keys=False, default_flow_style=False, width=100, allow_unicode=True)


def statement_descriptor(brand: str, kind_suffix: str) -> str:
    """Stripe: <=22 chars, [a-zA-Z0-9 ], no special chars, no 'test'."""
    clean = "".join(c for c in brand.upper() if c.isalnum() or c == " ").strip()
    combo = f"{clean} {kind_suffix}"
    return combo[:22]


class StripeClient:
    """Thin Stripe wrapper. Reads are always live (safe). Writes are gated by dry_run."""

    def __init__(self, secret_key: str, dry_run: bool):
        self.secret_key = secret_key
        self.dry_run = dry_run
        self._client = httpx.Client(
            base_url=STRIPE_API,
            headers={"Authorization": f"Bearer {secret_key}"},
            timeout=30,
        )
        self._dryrun_counter = 0

    def close(self):
        self._client.close()

    def _flatten(self, data: Any, prefix: str = "") -> list[tuple[str, str]]:
        """Flatten nested dicts/lists into Stripe's form encoding (key[sub][0]=val)."""
        items: list[tuple[str, str]] = []
        if isinstance(data, dict):
            for k, v in data.items():
                key = f"{prefix}[{k}]" if prefix else k
                items.extend(self._flatten(v, key))
        elif isinstance(data, list):
            for i, v in enumerate(data):
                key = f"{prefix}[{i}]"
                items.extend(self._flatten(v, key))
        elif data is None or data is False:
            if data is False:
                items.append((prefix, "false"))
        elif data is True:
            items.append((prefix, "true"))
        else:
            items.append((prefix, str(data)))
        return items

    def get(self, path: str, params: dict | None = None) -> dict:
        r = self._client.get(path, params=params or {})
        if r.status_code >= 400:
            raise RuntimeError(f"Stripe GET {path} -> {r.status_code}: {r.text[:200]}")
        return r.json()

    def post(self, path: str, data: dict) -> dict:
        if self.dry_run:
            print(f"    [dry-run] POST {path}")
            for k, v in list(data.items())[:4]:
                print(f"              {k} = {v!r}")
            self._dryrun_counter += 1
            return {
                "id": f"dryrun_{self._dryrun_counter}",
                "url": f"https://buy.stripe.com/DRYRUN_{self._dryrun_counter}",
                **data,
            }
        form = dict(self._flatten(data))
        r = self._client.post(path, data=form)
        if r.status_code >= 400:
            raise RuntimeError(f"Stripe POST {path} -> {r.status_code}: {r.text[:400]}")
        return r.json()


def find_by_metadata(client: StripeClient, endpoint: str, vertical: str, kind: str,
                      interval: str | None = None, active: bool = True) -> dict | None:
    """List + filter by metadata client-side (Stripe has no metadata filter in list API)."""
    params: dict[str, Any] = {"limit": 100}
    if active is not None:
        params["active"] = "true" if active else "false"
    for page in range(3):  # cap pagination at 3 pages = 300 items
        results = client.get(endpoint, params=params)
        for r in results.get("data", []):
            meta = r.get("metadata") or {}
            if meta.get("vertical") == vertical and meta.get("kind") == kind:
                if interval is None or meta.get("interval") == interval:
                    return r
        if not results.get("has_more"):
            break
        params["starting_after"] = results["data"][-1]["id"]
    return None


def ensure_product(client: StripeClient, ctx: SyncContext, kind: str, display_suffix: str) -> dict:
    existing = find_by_metadata(client, "/products", ctx.vertical, kind, active=True)
    if existing:
        ctx.planned.append(PlannedAction("reuse", "product", kind, "-", f"{existing['id']} ({existing['name']})"))
        return existing
    name = f"{ctx.brand} — {display_suffix}"
    description = PRODUCT_DESCRIPTIONS[kind].format(brand=ctx.brand)
    ctx.planned.append(PlannedAction("create", "product", kind, "-", name))
    return client.post("/products", {
        "name": name,
        "description": description,
        "url": f"https://{ctx.domain}/pricing",
        "metadata": {
            "vertical": ctx.vertical,
            "kind": kind,
            "brand": ctx.brand,
            "domain": ctx.domain,
        },
    })


def ensure_price(client: StripeClient, ctx: SyncContext, product: dict, kind: str,
                 interval: str, recurring_interval: str, amount_usd: int) -> dict:
    """Find an active price on this product matching amount+interval, else create."""
    amount_cents = amount_usd * 100
    # Skip the GET if the product is a dry-run placeholder (no prices could exist yet)
    if not product["id"].startswith("dryrun_"):
        results = client.get("/prices", params={"limit": 100, "product": product["id"], "active": "true"})
        for p in results.get("data", []):
            meta = p.get("metadata") or {}
            if (meta.get("vertical") == ctx.vertical and
                    meta.get("kind") == kind and
                    meta.get("interval") == interval and
                    p.get("unit_amount") == amount_cents and
                    (p.get("recurring") or {}).get("interval") == recurring_interval):
                ctx.planned.append(PlannedAction(
                    "reuse", "price", kind, interval,
                    f"{p['id']} (${amount_usd}/{recurring_interval})"
                ))
                return p
    ctx.planned.append(PlannedAction("create", "price", kind, interval, f"${amount_usd}/{recurring_interval}"))
    nickname = f"{ctx.brand} {kind.replace('_', ' ').title()} — {interval.title()}"
    return client.post("/prices", {
        "product": product["id"],
        "currency": "usd",
        "unit_amount": amount_cents,
        "recurring": {"interval": recurring_interval},
        "nickname": nickname,
        "tax_behavior": "exclusive",
        "metadata": {
            "vertical": ctx.vertical,
            "kind": kind,
            "interval": interval,
            "amount_usd": str(amount_usd),
        },
    })


def ensure_payment_link(client: StripeClient, ctx: SyncContext, price: dict, kind: str,
                        interval: str, statement_suffix: str) -> dict:
    """Find active payment link matching this vertical/kind/interval AND pointing at this
    exact price. If a stale link exists (different price), deactivate + create new."""
    # Dry-run placeholder price means no existing links can match
    if not price["id"].startswith("dryrun_"):
        results = client.get("/payment_links", params={"limit": 100, "active": "true"})
        for link in results.get("data", []):
            meta = link.get("metadata") or {}
            if (meta.get("vertical") == ctx.vertical and
                    meta.get("kind") == kind and
                    meta.get("interval") == interval):
                # Match — check price
                line_items = (link.get("line_items") or {}).get("data") or []
                current_price = line_items[0]["price"]["id"] if line_items else None
                if current_price == price["id"]:
                    ctx.planned.append(PlannedAction("reuse", "payment_link", kind, interval, link["url"]))
                    return link
                # Stale — deactivate
                ctx.planned.append(PlannedAction("deactivate-link", "payment_link", kind, interval,
                                                  f"{link['id']} (superseded)"))
                client.post(f"/payment_links/{link['id']}", {"active": "false"})

    ctx.planned.append(PlannedAction("create", "payment_link", kind, interval, f"for {price['id']}"))
    descriptor = statement_descriptor(ctx.brand, statement_suffix)
    return client.post("/payment_links", {
        "line_items": [{"price": price["id"], "quantity": 1}],
        # NOTE: customer_creation + invoice_creation are implicit for recurring
        # prices (subscriptions); Stripe rejects them on subscription payment
        # links. Keep only fields that work for both one-time and recurring.
        "billing_address_collection": "auto",
        "tax_id_collection": {"enabled": True},
        "payment_method_collection": "always",
        # Stripe's default hosted confirmation page is shown after completion.
        # To redirect to a branded /thanks page later, add an after_completion block.
        "subscription_data": {
            "description": f"{ctx.brand} — {kind.replace('_', ' ').title()} ({interval})",
            "metadata": {
                "vertical": ctx.vertical,
                "kind": kind,
                "interval": interval,
                "domain": ctx.domain,
            },
        },
        "metadata": {
            "vertical": ctx.vertical,
            "kind": kind,
            "interval": interval,
        },
    })


def sync_vertical(slug: str, execute: bool) -> int:
    secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not secret_key:
        print("error: STRIPE_SECRET_KEY not set in env", file=sys.stderr)
        return 2
    if not secret_key.startswith(("sk_", "rk_")):
        print(f"error: STRIPE_SECRET_KEY must start with sk_ or rk_ (got {secret_key[:6]}...)", file=sys.stderr)
        return 2

    config = load_yaml(slug)
    pricing = config.get("pricing") or {}
    if not pricing:
        print(f"error: no `pricing` block in configs/{slug}.yaml", file=sys.stderr)
        return 2
    brand = config.get("brand_name") or slug
    domain = config.get("domain") or f"{slug}.com"

    ctx = SyncContext(vertical=slug, brand=brand, domain=domain, pricing=pricing)
    client = StripeClient(secret_key, dry_run=not execute)

    print(f"\n=== Stripe sync for '{slug}' ({brand}, {domain}) ===")
    print(f"  Mode:  {'LIVE (--execute)' if execute else 'DRY-RUN  (pass --execute to apply)'}")
    print(f"  Key:   {secret_key[:7]}... ({'live' if '_live_' in secret_key else 'test'})")
    print(f"  Pricing:")
    for kind, prefix, _, _ in TIERS:
        for interval, yaml_field, _ in INTERVALS:
            amount = pricing.get(f"{prefix}_{yaml_field}")
            print(f"    {kind:9s} / {interval:7s}  ${amount}/{interval[:-2]}")

    try:
        for kind, prefix, display_suffix, stmt_suffix in TIERS:
            product = ensure_product(client, ctx, kind, display_suffix)
            config[f"stripe_{prefix}_product_id"] = product["id"]
            for interval, yaml_field, recurring_interval in INTERVALS:
                amount = pricing.get(f"{prefix}_{yaml_field}")
                if not amount:
                    print(f"  WARN: pricing.{prefix}_{yaml_field} missing, skipping {kind}/{interval}")
                    continue
                price = ensure_price(client, ctx, product, kind, interval, recurring_interval, amount)
                config[f"stripe_{prefix}_{interval}_price_id"] = price["id"]
                link = ensure_payment_link(client, ctx, price, kind, interval, stmt_suffix)
                config[f"stripe_{prefix}_{interval}_link"] = link["url"]
    except Exception as e:
        client.close()
        print(f"\nERROR: {e}", file=sys.stderr)
        print("\n  Partial plan:")
        for a in ctx.planned:
            print(a)
        return 1
    client.close()

    print("\n  Planned actions:")
    for a in ctx.planned:
        print(a)

    if execute:
        dump_yaml(slug, config)
        print(f"\n✓ Live sync complete. configs/{slug}.yaml updated with Stripe IDs and URLs.")
        print("  NOTE: yaml was rewritten via pyyaml — inspect the diff before committing.")
    else:
        print("\n(dry-run; no yaml writes, no Stripe writes. Pass --execute to apply.)")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument("--vertical", required=True, help="Vertical slug (matches configs/<slug>.yaml)")
    parser.add_argument("--execute", action="store_true", help="Apply changes (default: dry-run)")
    args = parser.parse_args()
    sys.exit(sync_vertical(args.vertical, args.execute))


if __name__ == "__main__":
    main()
