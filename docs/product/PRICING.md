# PRICING: URJA — Renewable Asset Management Boilerplate

**Status**: Final
**Author**: Alex (Product Manager)
**Last Updated**: 2026-07-22
**Version**: 1.0

---

## 1. Pricing Philosophy

URJA is a **boilerplate**, not a SaaS platform. This distinction shapes every pricing decision.

### One-Time Purchase, No Subscriptions

| Model | URJA Approach | Why |
|-------|--------------|-----|
| **Pricing model** | One-time purchase | Buyers own the code forever. No recurring billing, no lock-in. |
| **Hosting cost** | $0 (buyer-hosted) | We don't operate servers. No cloud bill, no SLA obligations. |
| **Support model** | Best-effort (Basic), Priority (Pro), Consulting (Enterprise) | Buyers pay for code, not ongoing service. |
| **Revenue model** | Transactional (per sale) | Cash-flow positive from day 1. Predictable with volume. |

### Why This Works for Boilerplate

1. **Developer buying behavior** — Developers and consultants are conditioned to pay $129–$499 for boilerplates (ShipFast, Supastarter, Tailwind UI, etc.). The price is an investment in productivity, not an operating expense.
2. **Zero direct competition** — No other renewable energy boilerplate exists. Generic boilerplates (ShipFast, Supastarter) have zero energy domain logic. Enterprise solutions (Power Factors, Fluence) cost 100–1000x more.
3. **Buyer economics** — A consultant billing $150/hr who saves 3 months of build time recovers the $149 cost in ~1 hour of billable work. The ROI is immediate and obvious.
4. **No delivery costs** — Gumroad handles payment processing, file delivery, and license key generation. Each additional sale costs us ~8.5% + $0.30 in fees. At $149, that's ~$13 — negligible for a digital product.
5. **Infinite scalability** — 10 sales and 10,000 sales cost the same to fulfill. There are no servers to scale, no support team to hire, no infrastructure to maintain.

### What We Are NOT Selling

- **Not a managed service** — No uptime guarantees, no infrastructure, no SLAs.
- **Not consulting** — Code is self-service. Enterprise tier includes 1 hour of consulting, but ongoing services are separate engagements.
- **Not compliance certification** — We provide the MRV pipeline. Certification against Verra, Gold Standard, or CDM is the buyer's responsibility.

---

## 2. Tier Breakdown

### URJA Basic — $149

| Category | Included |
|----------|----------|
| **Backend** | Full FastAPI API (all endpoints, services, models) |
| **Database** | Complete SQLAlchemy 2.0 schema + TimescaleDB hypertables + Alembic migrations |
| **Frontend** | Next.js 16 dashboard with KPI cards, generation curves, asset map, carbon portfolio, health alerts |
| **Seed Data** | 12-month sample dataset for a 50MW solar farm (2.9M+ rows) |
| **Deployment** | Docker Compose configuration (5 containers) |
| **Carbon MRV** | Digital credit pipeline with IPMVP methodology, audit trail, ESG export |
| **Dispatch** | Curtailment-aware dispatch optimization rules engine |
| **Documentation** | ARCHITECTURE.md, API.md, DATABASE.md, DEPLOYMENT.md |
| **License** | Commercial license — own-product use, no redistribution/resale |
| **Updates** | Access to all v1.x releases |

**Target buyer**: Developers entering energy, clean energy consultants, farm operators.

### URJA Pro — $249

Everything in Basic, plus:

| Category | Included |
|----------|----------|
| **TUI Dashboard** | Full Textual terminal UI: Overview, Curtailment, Carbon, Health screens. Runs in terminal AND browser. |
| **ML Health Models** | Anomaly detection using z-score + moving average deviation. Configurable alert thresholds. |
| **Priority GitHub Support** | Issues tagged `pro-priority` answered within 24 hours (business days). |
| **Advanced Analytics** | Additional dashboard views: trend analysis, comparative period-over-period reporting. |
| **Custom Alert Rules** | Create alert rules combining multiple metrics (temperature + power drop + time-of-day). |

**Target buyer**: System integrators, operators needing health monitoring, consultants wanting TUI for ops teams.

### URJA Enterprise — $499

Everything in Pro, plus:

| Category | Included |
|----------|----------|
| **White-Label License** | Full commercial license for resale. Rebrand as your own product. Remove all URJA branding. |
| **Private Repository** | Dedicated private GitHub repo with your branding. No other buyers have access. |
| **1-Hour Consulting Call** | Video call with the engineering lead. Architecture review, deployment planning, customization guidance. |
| **Custom Integration Support** | Email-based guidance for integrating URJA with existing SCADA/EMS systems. |
| **Team License** | Unlimited team members within your organization. |

**Target buyer**: System integrators reselling URJA to end clients, larger operators with in-house teams.

### Feature Comparison Table

| Feature | Basic ($149) | Pro ($249) | Enterprise ($499) |
|---------|:-----------:|:---------:|:---------------:|
| FastAPI backend | ✅ | ✅ | ✅ |
| Database schema + migrations | ✅ | ✅ | ✅ |
| Next.js 16 dashboard | ✅ | ✅ | ✅ |
| KPI cards + generation curves | ✅ | ✅ | ✅ |
| Asset map (Leaflet) | ✅ | ✅ | ✅ |
| Carbon MRV pipeline | ✅ | ✅ | ✅ |
| Dispatch optimization engine | ✅ | ✅ | ✅ |
| Seed data (50MW, 12mo) | ✅ | ✅ | ✅ |
| Docker Compose | ✅ | ✅ | ✅ |
| Documentation suite | ✅ | ✅ | ✅ |
| Sample SCADA integrations | ✅ | ✅ | ✅ |
| **TUI dashboard (Textual)** | ❌ | ✅ | ✅ |
| **ML anomaly detection** | ❌ | ✅ | ✅ |
| **Priority support (<24h)** | ❌ | ✅ | ✅ |
| **White-label license** | ❌ | ❌ | ✅ |
| **Private repo** | ❌ | ❌ | ✅ |
| **1-hour consulting call** | ❌ | ❌ | ✅ |
| **Custom integration guidance** | ❌ | ❌ | ✅ |
| **Unlimited team members** | ❌ | ❌ | ✅ |

---

## 3. What's NOT Included

### All Tiers

| Exclusion | Rationale |
|-----------|-----------|
| **Hosted infrastructure** | URJA is self-hosted. We do not operate servers, databases, or any cloud infrastructure. |
| **Service-level agreements (SLAs)** | No uptime guarantees, no response-time commitments (except Pro priority support for GitHub issues). |
| **Custom development** | The codebase is provided as-is. Custom features, integrations, or modifications are buyer-responsible. |
| **Regulatory compliance audits** | We provide documentation and security best practices, but compliance certification (SOC 2, ISO 27001, etc.) is the buyer's responsibility. |
| **Credit certification / registry filing** | URJA generates audit-ready MRV data. Filing with Verra, Gold Standard, or other registries is the buyer's responsibility. |
| **Hardware/SCADA gateways** | Sample integration scripts are provided. Physical gateway deployment and hardware compatibility are buyer-responsible. |
| **Mobile app** | No native mobile application. The web dashboard is responsive but not mobile-optimized. |
| **Phone support** | Support is via GitHub Issues only. No phone, Slack, or email support. |
| **Training / onboarding** | Documentation and tutorials are provided. Live training sessions are not included (available as a consulting add-on). |

### Basic Exclusions

| Exclusion | Available In |
|-----------|-------------|
| TUI dashboard | Pro ($249) |
| ML health models (anomaly detection) | Pro ($249) |
| Priority support (<24h) | Pro ($249) |
| White-label license | Enterprise ($499) |
| Private repository | Enterprise ($499) |
| Consulting call | Enterprise ($499) |

---

## 4. Revenue Projections

### Assumptions

| Parameter | Conservative | Moderate | Optimistic |
|-----------|:-----------:|:--------:|:---------:|
| Monthly sales volume | 50 | 100 | 200 |
| Basic ($149) sales mix | 60% (30 units) | 50% (50 units) | 40% (80 units) |
| Pro ($249) sales mix | 30% (15 units) | 35% (35 units) | 40% (80 units) |
| Enterprise ($499) sales mix | 10% (5 units) | 15% (15 units) | 20% (40 units) |
| Average selling price (ASP) | $197 | $207 | $233 |
| Weighted ASP (used) | **$199** | **$199** | **$199** |

### Monthly Revenue

| Scenario | Units/Mo | ASP | Gross Revenue | Gumroad Fees (8.5% + $0.30) | Net Revenue |
|----------|:-------:|:---:|:------------:|:--------------------------:|:----------:|
| **Conservative** | 50 | $199 | $9,950 | ~$872 | **~$9,078** |
| **Moderate** | 100 | $199 | $19,900 | ~$1,720 | **~$18,180** |
| **Optimistic** | 200 | $199 | $39,800 | ~$3,440 | **~$36,360** |

### Detailed Breakdown

#### Conservative (50 sales/month)

| Tier | Units | Unit Price | Gross Revenue |
|------|:----:|:----------:|:------------:|
| Basic | 30 | $149 | $4,470 |
| Pro | 15 | $249 | $3,735 |
| Enterprise | 5 | $499 | $2,495 |
| **Total** | **50** | **$199 avg** | **$9,950** |
| Gumroad fees (8.5% + $0.30/unit) | | | -$862 |
| **Net monthly revenue** | | | **$9,088** |
| **Annual net revenue** | | | **$109,056** |

#### Moderate (100 sales/month)

| Tier | Units | Unit Price | Gross Revenue |
|------|:----:|:----------:|:------------:|
| Basic | 50 | $149 | $7,450 |
| Pro | 35 | $249 | $8,715 |
| Enterprise | 15 | $499 | $7,485 |
| **Total** | **100** | **$199 avg** | **$23,650** |
| Gumroad fees (8.5% + $0.30/unit) | | | -$2,040 |
| **Net monthly revenue** | | | **$21,610** |
| **Annual net revenue** | | | **$259,320** |

#### Optimistic (200 sales/month)

| Tier | Units | Unit Price | Gross Revenue |
|------|:----:|:----------:|:------------:|
| Basic | 80 | $149 | $11,920 |
| Pro | 80 | $249 | $19,920 |
| Enterprise | 40 | $499 | $19,960 |
| **Total** | **200** | **$199 avg** | **$51,800** |
| Gumroad fees (8.5% + $0.30/unit) | | | -$4,460 |
| **Net monthly revenue** | | | **$47,340** |
| **Annual net revenue** | | | **$568,080** |

### Time to Revenue Targets

| Scenario | Monthly Net Revenue | Months to $100K | Months to $500K |
|----------|:------------------:|:---------------:|:---------------:|
| Conservative | ~$9,100 | ~11 | ~55 |
| Moderate | ~$21,600 | ~5 | ~23 |
| Optimistic | ~$47,300 | ~3 | ~11 |

### Scaling Dynamics

Revenue scales linearly with sales volume because there are **zero marginal delivery costs**. Each additional sale requires:
- No additional infrastructure
- No additional support staffing (up to ~500 sales/month)
- No additional content creation

This is the fundamental economics advantage of boilerplate over SaaS: at $199 ASP, every 100 incremental sales adds ~$18,000/month in net revenue at ~95% gross margin.

---

## 5. Competitive Pricing Comparison

### Direct Competitors (Boilerplate Market)

| Product | Price Range | Domain | Business Model | Value per Dollar |
|---------|:----------:|--------|:--------------:|:----------------:|
| **URJA Basic** | **$149** | Renewable energy | One-time | Domain-specific models × production-ready code × documentation |
| **URJA Pro** | **$249** | Renewable energy | One-time | Above + TUI + ML + priority support |
| **URJA Enterprise** | **$499** | Renewable energy | One-time | Above + white-label + private repo + consulting |
| ShipFast | $129–$199 | Generic SaaS | One-time | Generic auth + payments + emails |
| Supastarter | $100–$249 | Generic SaaS | One-time | Generic auth + payments + emails + team |
| Tailwind UI | $149–$299 | UI components | One-time | CSS component library |
| Gravity UI | $79–$149 | UI components | One-time | CSS component library |

**URJA's position**: Priced at parity with generic boilerplates but delivers **domain-specific value** that would cost $50K+ to build from scratch. A developer buying ShipFast gets auth pages and Stripe integration. A developer buying URJA gets a complete renewable energy control plane with carbon credit pipeline.

### Indirect Competitors (Enterprise SaaS)

| Product | Annual Cost | Buyer | URJA Alternative Value |
|---------|:----------:|-------|----------------------|
| Power Factors Unity | $50K–$150K+/year | 500MW+ utilities | $149–$499 for 10–200MW operators |
| Fluence Mosaic | $100K–$500K+/year | 500MW+ utilities | $249 (Pro) for dispatch optimization |
| Wärtsilä GEMS | $100K–$500K+/year | Utility-scale | Not a direct competitor (different market) |
| AlsoEnergy | $30K–$80K+/year | 50MW+ operators | $149 (Basic) covers same monitoring use case |
| Draker (BayWa r.e.) | $20K–$60K+/year | Commercial solar | $149 for equivalent dashboard functionality |

**URJA's position**: 99.8% cheaper than enterprise alternatives. The trade-off: no support, no hosted infrastructure, no compliance certifications. For the target buyer (developers, consultants, small operators), this trade-off is acceptable — they have the technical capability to self-host and customize.

### Build vs. Buy Economics

| Build Approach | Estimated Cost | Timeline | Risk |
|---------------|:-------------:|:--------:|:----:|
| Build in-house (junior team) | $30K–$80K | 6–12 months | High — team may not have energy domain knowledge |
| Build in-house (senior team) | $80K–$200K | 4–8 months | Medium — expensive but feasible |
| Hire consultant to build | $50K–$150K | 3–6 months | Medium — quality depends on consultant |
| **Buy URJA Basic** | **$149** | **5 minutes** | **Low — 2.9M-row seed data proves it works** |

**ROI for a consultant**:
- Time saved per client engagement: 3–6 months
- Billable rate: $150–$250/hr
- Value of time saved: $72K–$240K
- URJA Basic cost: $149
- **ROI: 48,300%–161,000%**

### Positioning Summary

| Comparison | URJA Message |
|-----------|-------------|
| vs. Generic boilerplates (ShipFast, Supastarter) | "You get energy domain models, not just auth pages. Same price, 100x more value." |
| vs. Enterprise SaaS (Power Factors, Fluence) | "99.8% cheaper. Self-hosted. Fully customizable. Built for 10–200MW, not 500MW+." |
| vs. Build in-house | "$149 vs. $50K+. 5-minute deploy vs. 6-month build. Seed data proves it works." |
| vs. Do nothing | "Curtailment costs grow every year. URJA shows you exactly how much you're losing." |

---

## 6. Discount Strategy

### Launch Discount (First 30 Days)

| Offer | Price | Discount | Terms |
|-------|:----:|:--------:|-------|
| Basic Launch | **$99** | 34% off $149 | First 50 buyers. One-time discount. |
| Pro Launch | **$179** | 28% off $249 | First 50 buyers. One-time discount. |
| Enterprise Launch | **$399** | 20% off $499 | First 20 buyers. One-time discount. |

**Rationale**: Launch discounts serve two purposes: (a) generate initial social proof and reviews, and (b) validate demand at lower price sensitivity. After 50/20 units sold, prices revert to standard.

**Impact on revenue**: If all first-50 buyers take launch pricing, first-month revenue is ~$6,250 (vs. $9,950 standard). The $3,700 discount is a marketing cost — cheaper than ads.

### Early Adopter Pricing (Days 31–90)

| Offer | Price | Discount | Terms |
|-------|:----:|:--------:|-------|
| Early Adopter Basic | **$119** | 20% off $149 | First 6 months of launches. |
| Early Adopter Pro | **$199** | 20% off $249 | First 6 months of launches. |
| Early Adopter Enterprise | **$399** | 20% off $499 | First 6 months of launches. |

**Rationale**: Reward early buyers without devaluing the product. 20% off is meaningful but not "cheap." Creates urgency with time-limited pricing.

### Bundle Pricing

| Bundle | Components | Bundle Price | Savings vs. Separate |
|--------|-----------|:-----------:|:-------------------:|
| URJA Pro + 2-Hour Consulting | Pro ($249) + 2h consulting ($500 value) | **$599** | $150 |
| URJA Enterprise + 5-Hour Consulting | Enterprise ($499) + 5h consulting ($1,250 value) | **$1,499** | $250 |
| URJA Basic + Pro Upgrade Voucher | Basic ($149) + future Pro at $149 (vs $249) | **$199** | $100 (if they upgrade) |

**Rationale**: Consulting bundles increase ASP while keeping the core product accessible. The upgrade voucher reduces upgrade friction — Basic buyers lock in the lower upgrade price.

### Volume Licensing

| Quantity | Discount per Unit | Eligibility |
|:--------:|:----------------:|------------|
| 5–9 licenses | 10% off | Single organization, verified email domain |
| 10–24 licenses | 15% off | Single organization, verified email domain |
| 25+ licenses | 20% off + dedicated onboarding | Contact for custom pricing |

**Rationale**: Consulting firms and system integrators may need multiple licenses for their team. Volume pricing encourages enterprise adoption without cannibalizing individual sales.

### What We Don't Do

- No coupon codes or perpetual sales (Gumroad's built-in discount engine should remain unused except for launch/promotional periods)
- No affiliate program in v1 (Lemon Squeezy supports affiliates; Gumroad does not. If affiliate demand emerges, migrate to Lemon Squeezy)
- No "lifetime" discounts — we do have one-time pricing, so every purchase is effectively lifetime

---

## 7. Renewal / Upgrade Path

### Upgrade Pricing

| From | To | Upgrade Price | Difference Paid |
|------|:--:|:------------:|:--------------:|
| Basic ($149) | Pro ($249) | $100 | Buyer pays the difference |
| Basic ($149) | Enterprise ($499) | $350 | Buyer pays the difference |
| Pro ($249) | Enterprise ($499) | $250 | Buyer pays the difference |
| Basic (Launch $99) | Pro (Launch $179) | $80 | Difference at launch pricing |
| Basic (Launch $99) | Enterprise ($499) | $400 | Difference (full Enterprise price — launch Basic is not eligible for stacked discounts) |

**Implementation**: Upgrade codes generated manually or via Gumroad's license key system. Buyer purchases the upgrade tier, we issue a new license key and grant access to the upgraded repository/docs.

**Policy**: Upgrades are permanent. Buyers can access both tiers' content after upgrade. No downgrade refunds.

### Crossgrade Pricing

| From | To | Crossgrade Price | Rationale |
|------|:--:|:--------------:|-----------|
| ShipFast | URJA Basic | $99 (vs $149) | Validate conversion from generic to energy-specific. Show the buyer's email + receipt. |
| Supastarter | URJA Basic | $99 (vs $149) | Same as above. Limited-time crossgrade offer (first 90 days). |

**Rationale**: A small number of ShipFast/Supastarter buyers may also need energy-specific tooling. The crossgrade discount is a low-cost experiment to test whether generic boilerplate buyers convert to domain-specific.

### Add-On Purchases (Post-Purchase)

| Add-On | Price | Available To | Description |
|--------|:----:|:-----------:|-------------|
| Extra consulting hour | $250/hour | Pro, Enterprise | Video call + follow-up notes |
| Custom integration | $500–$2,500 (per scope) | Enterprise | Custom SCADA connector, data migration, or feature extension |
| Deployment assistance | $500 | Enterprise | One-time setup support on buyer's infrastructure |
| Branding package | $200 | Basic, Pro | Custom logo, colors, domain setup guidance (Enterprise includes this) |

**Rationale**: Add-ons increase LTV without changing core product pricing. Consulting hours are the highest-margin add-on — pure knowledge transfer at $250/hr.

### Price Lock Guarantee

Early buyers who purchase at launch or early adopter pricing receive a **price lock** — if we increase prices in the future, they retain access to all features at their purchased tier for life. Future major version upgrades (v2.0, v3.0) may require a nominal upgrade fee ($49–$99), communicated at least 60 days in advance.

---

## 8. Payment Processing

### Gumroad Fee Structure

| Fee Component | Amount | Notes |
|:------------:|:-----:|-------|
| Transaction fee | 8.5% of sale price | Industry standard for digital product platforms |
| Fixed fee | $0.30 per transaction | Per-purchase processing fee |
| Total fee (Basic $149) | $12.97 | 8.7% effective rate |
| Total fee (Pro $249) | $21.47 | 8.6% effective rate |
| Total fee (Enterprise $499) | $42.72 | 8.6% effective rate |

### Net Revenue Per Sale

| Tier | Gross Price | Gumroad Fee | Net to Us | Margin |
|:----:|:----------:|:----------:|:---------:|:-----:|
| Basic | $149 | $12.97 | **$136.03** | 91.3% |
| Pro | $249 | $21.47 | **$227.53** | 91.4% |
| Enterprise | $499 | $42.72 | **$456.28** | 91.4% |
| Weighted avg | $199 | $17.22 | **$181.78** | 91.3% |

### Launch Discount Net Revenue

| Tier | Discounted Price | Gumroad Fee | Net to Us | Margin |
|:----:|:---------------:|:----------:|:---------:|:-----:|
| Basic Launch | $99 | $8.72 | **$90.28** | 91.2% |
| Pro Launch | $179 | $15.52 | **$163.48** | 91.3% |
| Enterprise Launch | $399 | $34.22 | **$364.78** | 91.4% |

### Payment Methods Accepted

Gumroad supports:
- Credit/debit cards (Visa, Mastercard, Amex, Discover)
- PayPal
- Apple Pay
- Google Pay
- Buy Now, Pay Later (Afterpay, Klarna, etc.)

**Payout schedule**: Gumroad pays out on a weekly cadence (every Friday) via bank transfer. Payouts include all settled transactions from the previous week. Minimum payout threshold is $10.

### Tax Handling

| Tax | Responsibility | Gumroad Handling |
|:---:|:-------------:|:----------------:|
| US Sales Tax | Buyer | Gumroad collects and remits automatically |
| EU VAT | Buyer | Gumroad collects and remits (based on buyer location) |
| UK VAT | Buyer | Gumroad collects and remits |
| Australian GST | Buyer | Gumroad collects and remits |
| Other jurisdictions | Buyer | Buyer may owe local taxes; we do not collect |

**Impact on pricing**: Prices listed are pre-tax. Gumroad displays the final price (including applicable taxes) to the buyer at checkout. For most buyers (individuals in the US), no additional tax applies.

### Why Gumroad Over Alternatives

| Platform | Fee | Key Advantage | Key Disadvantage |
|----------|:---:|:-------------:|:----------------:|
| **Gumroad** | 8.5% + $0.30 | Proven for boilerplates. Simple. Buyers trust it. | No affiliate system. No EU VAT automation (they do handle it). |
| Lemon Squeezy | 5% + $0.50 | Lower fees. Affiliate support. EU VAT handling. | Newer platform. Smaller buyer trust. Fewer indie-hacker case studies. |
| Paddle | 5% + $0.50 | Full tax compliance globally. | Higher minimums. More complex setup. |
| Stripe direct | 2.9% + $0.30 | Lowest fees (after platform costs). | Requires custom storefront. No license management. No file delivery. |

**Recommendation**: Start with Gumroad. The 8.5% fee is acceptable for v1 because Gumroad removes all operational complexity (file delivery, license keys, buyer management, tax handling). If monthly volume exceeds 200 sales, evaluate Lemon Squeezy or direct Stripe integration to recover ~3–4% in fees (~$600–$1,600/month savings at 200 sales).

---

## 9. Refund Policy

### Standard Policy: 30-Day Money-Back Guarantee

**Policy**: Full refund available within 30 days of purchase, no questions asked.

**Mechanism**: Buyers request refund via Gumroad's built-in refund system. Refunds are processed automatically for the first 30 days.

**Rationale**: 30-day refunds are the industry standard for boilerplates (ShipFast, Supastarter, Tailwind UI all offer 30-day guarantees). The expectation is that a buyer can evaluate the product within 30 days and confirm it meets their needs. A no-questions-asked policy builds trust and reduces purchase friction.

### Refund Rate Projections

| Scenario | Expected Refund Rate | Impact on Net Revenue |
|----------|:-------------------:|:--------------------:|
| Conservative | 5% | Reduces net revenue by ~$455/month at 50 sales |
| Moderate | 3% | Reduces net revenue by ~$546/month at 100 sales |
| Optimistic | 2% | Reduces net revenue by ~$908/month at 200 sales |

**Assumption**: Refund rates decrease over time as documentation improves and buyer expectations are better aligned with reality. The worst refund rates occur in the first 30 days post-launch.

### Refund Policy Details

| Scenario | Policy | Notes |
|----------|--------|-------|
| Request within 30 days | **Full refund** | No questions asked. Gumroad processes automatically. |
| Request after 30 days | **Case-by-case** | Considered if the buyer can demonstrate a product defect that prevents use. |
| Accidental duplicate purchase | **Full refund** | Processed same day. |
| Buyer never downloaded/unzipped | **Full refund** | At any time — no cost to us. |
| Upgraded then requested refund | **Refund at original tier price** | Buyer keeps Basic access after Pro refund minus $149. |
| Consulting call already delivered | **Partial refund** (product only) | Consulting is non-refundable once delivered. |

### Abuse Prevention

- Buyers who purchase, request refund, and re-purchase on the same email are flagged and reviewed manually.
- More than 2 refunds on the same payment method triggers manual review.
- No refund on consulting or custom integration work once delivered.

### Refund Messaging (Gumroad Listing)

> **30-Day Money-Back Guarantee**
>
> URJA comes with a 30-day unconditional refund. If the boilerplate doesn't meet your expectations — for any reason — request a refund via Gumroad and it's processed immediately.
>
> No questions. No hassle. No risk.
>
> After 30 days, refunds are considered on a case-by-case basis. If there's a product defect that prevents you from using URJA, we'll make it right regardless of timing.

---

## Appendix A: Price Sensitivity Analysis

### Willingness to Pay by Persona

| Persona | Max WTP | Anchor Price | Price Sensitivity | Recommendation |
|---------|:------:|:------------:|:-----------------:|:--------------:|
| Priya (Consultant) | $299 | Saves $72K–$96K per client | Low (high ROI) | Basic at $149 is an easy yes. Pro at $249 is justifiable. |
| Dmitri (Integrator) | $499 | Cuts project delivery by 60% | Low (enterprise budget) | Enterprise at $499 is a rounding error in a $500K project. |
| Elena (Operator) | $149 | $50K/year vs. $149 one-time | Medium | Basic is the right tier. Pro may be a stretch. |
| Marcus (Developer) | $99–$149 | Studies and portfolio value | High (personal spend) | Launch discount ($99) targets this persona. Basic at $149 is at the edge. |

### Price Elasticity Estimate

| Tier | Price | Price Cut to +50% Volume | Price Raise to -20% Volume | Recommended Action |
|:----:|:----:|:-----------------------:|:-------------------------:|:-----------------:|
| Basic | $149 | $99 (launch pricing) | $199 | Keep at $149 for v1. $99 launch. |
| Pro | $249 | $179 (launch pricing) | $299 | Keep at $249 for v1. $179 launch. |
| Enterprise | $499 | $399 (launch pricing) | $599 | Keep at $499 for v1. $399 launch. |

### Price Anchoring Strategy

The Enterprise tier at $499 exists primarily to make the Pro tier at $249 look reasonable. The Pro tier at $249 exists to make the Basic tier at $149 look like a bargain.

```
           Perceived Value
                ▲
                │                    Enterprise ($499)
                │                  ┌── White-label + private repo
                │                 ── 1-hour consulting call
                │                ╱
                │               ╱
                │              ●─────── Pro ($249)
                │             ── TUI dashboard + ML models
                │            ╱  Priority GitHub support
                │           ╱
                │          ●─────────── Basic ($149)
                │         ── Complete platform
                │        ╱  12-month seed data
                │       ╱  40K+ lines of code
                │      ●──────────────────────────► Price
```

The gap between Enterprise ($499) and the next alternative (custom build at $50K+) creates a powerful anchoring effect: every other tier looks cheap by comparison.

---

## Appendix B: Pricing FAQ (for Gumroad Listing)

**Q: Is this a one-time purchase or a subscription?**
A: One-time purchase. You own the code forever. No recurring fees.

**Q: Do I get updates?**
A: Yes. All v1.x releases are included in your purchase. Major version upgrades (v2.0+) may require a nominal upgrade fee, communicated in advance.

**Q: Can I get a refund?**
A: 30-day money-back guarantee. No questions asked.

**Q: Can I use URJA for multiple clients?**
A: Basic and Pro tiers include a single-organization license. The Enterprise tier includes a white-label license for resale to clients. Contact us for volume pricing.

**Q: Do you offer hosting?**
A: No. URJA is self-hosted via Docker Compose. You run it on your own infrastructure. We provide the deployment guide.

**Q: What support do you offer?**
A: Basic tier: best-effort via GitHub Issues. Pro tier: priority support (<24h response). Enterprise tier: priority support + 1-hour consulting call + custom integration guidance.

**Q: Can I upgrade from Basic to Pro later?**
A: Yes. You pay the difference ($100). Contact us for an upgrade link.

**Q: Is there a free tier?**
A: A public GitHub repo with limited features (Yield module only) will be available pre-launch. It demonstrates the code quality and architecture without giving away the full product.

---

## Appendix C: Revenue Sensitivity Analysis

### Impact of Changing ASP

| Scenario | Units/Mo | ASP | Gross Revenue | Net Revenue (after fees) |
|----------|:-------:|:---:|:------------:|:-----------------------:|
| Low ASP (more Basic sales) | 100 | $179 | $17,900 | $16,280 |
| Base ASP (model assumption) | 100 | $199 | $19,900 | $18,180 |
| High ASP (more Pro/Enterprise) | 100 | $229 | $22,900 | $20,980 |

**Observation**: Each $10 change in ASP at 100 units/month changes net revenue by ~$910/month ($10,920/year). Upselling Basic buyers to Pro is worth ~$100 per conversion — equivalent to half a Basic sale without acquiring a new buyer.

### Impact of Changing Volume

| Scenario | Units/Mo | ASP | Gross Revenue | Net Revenue | YoY Net Revenue |
|----------|:-------:|:---:|:------------:|:----------:|:--------------:|
| Stretch (survival) | 20 | $199 | $3,980 | $3,600 | $43,200 |
| Conservative | 50 | $199 | $9,950 | $9,088 | $109,056 |
| Moderate (target) | 100 | $199 | $19,900 | $18,180 | $218,160 |
| Optimistic | 200 | $199 | $39,800 | $36,360 | $436,320 |
| Viral (content snowballs) | 500 | $199 | $99,500 | $91,000 | $1,092,000 |

### Break-Even Analysis

URJA's development cost is estimated at ~$50K–$80K (8–12 weeks of a 2-person team at $150–$200/hr effective cost). Break-even analysis:

| Scenario | Break-Even Revenue | Months to Break-Even |
|----------|:-----------------:|:-------------------:|
| Conservative ($9K/mo net) | $65K (midpoint) | ~7 months |
| Moderate ($18K/mo net) | $65K | ~4 months |
| Optimistic ($36K/mo net) | $65K | ~2 months |

Even at conservative volumes, URJA reaches break-even within 7 months. At moderate volumes, it reaches break-even within a single quarter.

---

*PRICING v1.0 — Next step: Create Gumroad product listing, set up license key automation, and publish. Validate pricing via early-waitlist survey before GA launch.*
