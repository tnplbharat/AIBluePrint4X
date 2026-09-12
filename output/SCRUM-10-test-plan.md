# Test Plan — SCRUM-10: Requirement for cart module

| Field | Value |
| --- | --- |
| **Ticket** | SCRUM-10 — https://tnplbharat.atlassian.net/browse/SCRUM-10 |
| **Title** | Requirement for cart module |
| **Type / Status** | Story / In Review |
| **Priority** | Medium |
| **Project** | QA Testing |
| **Sprint / Fix version** | Not set on the ticket |
| **Components / Labels** | None |
| **Linked issues / Sub-tasks / Attachments** | None |
| **Created / Updated** | 2026-09-12 |
| **Source** | Jira Cloud REST API v3 (`/rest/api/3/issue/SCRUM-10`), fetched 2026-09-12 |
| **Document status** | DRAFT — awaiting human sign-off |

> **This plan is a draft, not an approved artifact.** It is derived from the ticket
> description alone. The ticket has **no acceptance-criteria section**, so scenarios are
> traced to description statements and to the gaps in Section 2 — not to agreed ACs.
> Nothing here is final until a human approves it.

---

## 1. Scope & Objectives

**In scope (as listed on the ticket):**

- Cart operations: add item, add multiple quantity, add multiple items, remove item, update quantity, empty cart.
- Cart persistence: across page refresh, and (conditionally) across tabs/windows.
- Pricing: subtotal, tax, shipping cost, total.
- Cart UI: line display, totals display, responsive layout, call-to-action buttons, UI error messages.
- Advanced (conditionally in scope): coupons, save-for-later, guest checkout, payment-gateway hand-off.
- Edge and negative cases: out of stock, large quantities, zero quantity, invalid input, session timeout.

**Objective:** confirm the cart computes and displays monetary values correctly for every
mutation and boundary condition, and that it degrades safely on invalid input, out-of-stock
items, and session loss.

**Highest-risk area is money.** Subtotal / tax / shipping / total arithmetic, rounding
precision, and whether server-side totals trust client-supplied quantities and prices. A defect
here is financial and reputational, so price-integrity cases are rated **P0** below even though
the ticket files calculations under "High Priority".

**Major unknown:** the application under test, its environment, and its test data are not
defined anywhere (G3–G6). This repository contains no cart implementation, so the module under
test is external to it.

---

## 2. Gaps & Questions for the author

Scored ✅ present · ⚠️ ambiguous · ❌ missing. Every ⚠️/❌ below is a question the author
needs to answer before execution. **This section is the most valuable output of this plan** —
it is cheaper to answer these now than to find the defects in production.

| ID | Item | Score | Question for the author |
| --- | --- | --- | --- |
| G1 | Acceptance criteria | ❌ | The story has no AC section. The description is a list of "verify that…" statements with no expected results, so nothing is objectively pass/fail. Will you supply ACs, or approve the traceability in Section 3 as a substitute? |
| G2 | User story / goal | ❌ | There is no "As a … I want … so that …". What is the user goal and the business outcome the cart must deliver? |
| G3 | Application & environment | ❌ | Which product, URL, build and browser matrix is under test, and how is the build deployed for QA? |
| G4 | Test data | ❌ | No catalog, prices, currency, tax rates, shipping rules or coupon codes are specified. Who supplies them, or should QA seed them? |
| G5 | Preconditions / setup | ❌ | Is a pre-seeded cart, a registered account, or a specific session configuration required to begin? |
| G6 | External integrations | ⚠️ | The shipping API and payment gateway are referenced but not named. Which sandbox endpoints and test modes apply? |
| G7 | "Remove the last item clears the cart (if applicable)" | ⚠️ | Is the empty-cart state a requirement, and what should it look like? |
| G8 | Cross-tab persistence "(if applicable – depends on your implementation)" | ⚠️ | Is cross-tab consistency in scope for this release, and should it be immediate or eventual? |
| G9 | Multi-currency "if your system supports multiple currencies" | ⚠️ | Single- or multi-currency? Which currencies, and what rounding/exchange rule? |
| G10 | Guest checkout "If guest checkout is supported" | ⚠️ | Is guest checkout in scope? Does a guest cart merge into the account on login? |
| G11 | Advanced features "Low Priority … depending on requirements" | ⚠️ | Are coupons, save-for-later, guest checkout and gateway integration in scope for this release, or explicitly deferred? |
| G12 | Unobservable wording | ⚠️ | "doesn't break the cart functionality", "accurately", "handle gracefully" — what is the observable expected result in each case? |
| G13 | Quantity bounds | ❌ | What are min/max quantity, per-item stock cap and total-cart cap? Is a quantity of 0 an error or a removal? |
| G14 | Non-functional requirements | ❌ | No performance, security/authorization, accessibility, i18n or logging requirements. Which apply? In particular: **can a user read or modify another user's cart (cart-id authorization)?** |
| G15 | Regression surface | ❌ | Which existing pages and flows are affected (product page, mini-cart, checkout, order history, promotions)? |
| G16 | Designs / mockups | ❌ | No mockups are linked for the cart, the empty state, or the error states. |
| G17 | Ownership & stability | ⚠️ | Reporter, assignee, components, sprint and fix version are all empty, and the status is "In Review". Who answers these questions, and is scope frozen? |
| G18 | Money rounding & precision | ❌ | Rounding rule per line vs per cart, tax rounding, and currency decimal handling are unspecified. |
| G19 | Concurrency & staleness | ❌ | Behaviour when the same cart is mutated from two sessions, when stock depletes mid-session, or when a price changes while an item sits in the cart. |

### Checklist roll-up

| Checklist area | ✅ | ⚠️ | ❌ |
| --- | --- | --- | --- |
| Functional | 0 | 4 | 2 |
| Data & environment | 0 | 1 | 3 |
| Non-functional | 0 | 1 | 4 |
| Cross-cutting | 0 | 1 | 3 |
| Clarity | 0 | 2 | 1 |
| **Total** | **0** | **9** | **13** |

Nothing on the checklist scored ✅. The ticket describes what to poke at, not what "correct"
means.

---

## 3. Test Scenarios

Priorities are a **proposal**. The ticket labels its own groups Must-Have / High / Medium /
Low / Important; the mapping keeps that intent but promotes money-integrity cases to P0.

- **P0** — blocks release: core cart operation broken, or financial/data integrity at risk.
- **P1** — significant functional or UX impact.
- **P2** — low impact, or scope-dependent (see G11).

`Trace` references description sections (D-I…D-V) or gaps (G#). Where the expected result
depends on an unanswered question it is marked **Spec needed**, not invented.

### 3.1 Core cart operations — P0 (D-I)

| ID | Scenario | Expected result | Pri | Trace |
| --- | --- | --- | --- | --- |
| C-01 | Add one item to an empty cart | Cart holds 1 line, qty 1, line subtotal = unit price | P0 | D-I |
| C-02 | Add the same item again | Existing line qty increments to 2; no duplicate line | P0 | D-I |
| C-03 | Add the same item with an explicit quantity of 5 | qty 5, subtotal = unit price × 5 | P0 | D-I |
| C-04 | Add two different items | Two distinct lines with correct independent quantities | P0 | D-I |
| C-05 | Add to cart from the product page | Cart reflects the item and quantity; cart count/badge reflects it | P0 | D-I |
| C-06 | Remove one line from a multi-line cart | That line is gone, other lines unchanged, totals recomputed | P0 | D-I |
| C-07 | Decrease quantity on a line with qty > 1 | Quantity drops by 1; totals recomputed | P0 | D-I |
| C-08 | Remove the only/last item | Cart reaches empty state per G7 — **Spec needed** | P0 | D-I, G7 |
| C-09 | Click "empty cart" on a populated cart | All lines removed, totals zero | P0 | D-I |
| C-10 | Increase quantity on an existing line | Line subtotal and cart totals increase correctly | P0 | D-I |
| C-11 | Refresh the page with items in cart | Items and quantities retained; totals recompute correctly | P0 | D-I |
| C-12 | Open the cart in a second tab after adding in the first | Consistency behaviour per G8 — **Spec needed** | P1 | D-I, G8 |
| C-13 | Mutate the cart, then log out and back in | Cart is account-bound or session-bound per G14 — **Spec needed** | P1 | D-I, G14 |

### 3.2 Price & calculation integrity — P0 (D-II)

| ID | Scenario | Expected result | Pri | Trace |
| --- | --- | --- | --- | --- |
| P-01 | Subtotal of a multi-line cart | Equals Σ(unit price × qty) for all lines | P0 | D-II |
| P-02 | Totals after each mutation (add / remove / qty change / empty) | Always recomputed; never stale | P0 | D-II |
| P-03 | Quantity reduced to 1 (boundary) | Line subtotal equals a single unit price | P0 | D-II |
| P-04 | Tax on a taxable cart | Matches a hand-calculated expected value for the configured rate | P0 | D-II, G4 |
| P-05 | Shipping cost per method | Matches the rule for weight / destination / method | P0 | D-II, G6 |
| P-06 | Total price | Equals subtotal + tax + shipping − discounts, verified by hand | P0 | D-II |
| P-07 | Rounding & precision | Consistent per-line/per-cart rounding; 2 dp currency; no float artefacts (e.g. 0.1 + 0.2) | P0 | G18 |
| P-08 | Zero-value cart (100% coupon, or a zero-price item) | Total is 0, never negative | P1 | D-II, D-IV |
| P-09 | Mixed-currency or currency switch | Consistent totals per G9 — **Spec needed** | P2 | D-II, G9 |

### 3.3 Cart UI — P1 (D-III)

| ID | Scenario | Expected result | Pri | Trace |
| --- | --- | --- | --- | --- |
| U-01 | Cart line rendering | Each line shows name, unit price, quantity, line subtotal | P1 | D-III |
| U-02 | Totals display | Totals shown clearly and match the computed values | P1 | D-III |
| U-03 | Responsive layout at 375 / 768 / 1440 px | Usable at all widths; no overflow or clipped controls | P1 | D-III |
| U-04 | CTA buttons: Add to Cart, Update Quantity, Remove Item, Checkout | Each performs its stated action | P1 | D-III |
| U-05 | Update Quantity with a typed value | Applied on blur/enter; invalid value rejected per G13 | P1 | D-III, G13 |
| U-06 | Add an out-of-stock item | User-visible error message; cart unchanged | P1 | D-III |
| U-07 | Empty cart representation | Empty-state message shown; Checkout unavailable | P1 | D-III, G7 |
| U-08 | Rapid repeated CTA clicks | No double submission or duplicated lines; controls disabled while in flight | P1 | D-III, D-V |
| U-09 | Keyboard-only and screen-reader use of cart controls | All controls reachable, labelled and operable | P2 | G14 |
| U-10 | Browser matrix (Chrome / Edge / Firefox / Safari) | Behaviour consistent per the matrix in G3 | P1 | D-III, G3 |

### 3.4 Edge cases & negative testing — P1 (D-V)

| ID | Scenario | Expected result | Pri | Trace |
| --- | --- | --- | --- | --- |
| E-01 | Item in cart goes out of stock before checkout | Clear messaging; checkout blocked for that line | P0 | D-V |
| E-02 | Quantity set to 0 | Error or removal, per G13 — **Spec needed** | P1 | D-V, G13 |
| E-03 | Negative quantity / decrement below 1 | Blocked or clamped; never a negative total | P0 | D-V |
| E-04 | Non-numeric quantity input (`abc`, `1e3`, `1.5`, emoji, whitespace, 1000-char string) | Rejected with a message; cart unchanged; no server error | P1 | D-V |
| E-05 | Very large quantity (999 / 10,000 / 999,999) | No overflow, NaN or Infinity; accepted or capped per G13 | P1 | D-V, G13 |
| E-06 | Quantity above available stock | Clamped or blocked with a message | P1 | D-V, G13 |
| E-07 | Session times out, then the user returns | Cart intact (per D-V) or defined behaviour per G14 | P1 | D-V |
| E-08 | Cookies/session storage cleared manually | Defined outcome: empty cart, or server-side cart restored | P2 | G14 |
| E-09 | Concurrent add/remove from two sessions | No duplicate lines, no lost updates | P1 | G19 |
| E-10 | Product price changes while an item sits in the cart | Cart reprices or holds the original price per G19 — **Spec needed** | P2 | G19 |
| E-11 | Tampered request (negative qty, client-supplied price or total) | Server rejects and recomputes authoritatively | P0 | G14 |
| E-12 | Injection attempts via quantity or coupon fields (SQLi / XSS) | Input sanitised and escaped; no script execution | P0 | G14 |
| E-13 | Locale or currency changed mid-session | Totals and formatting remain consistent | P2 | G9 |

### 3.5 Advanced features — P2 (D-IV, pending G11)

| ID | Scenario | Expected result | Pri | Trace |
| --- | --- | --- | --- | --- |
| A-01 | Apply a valid coupon | Discount applied to the correct base (subtotal vs total) | P2 | D-IV |
| A-02 | Apply an invalid, expired or already-used coupon | Clear error; no discount applied | P2 | D-IV |
| A-03 | Coupon boundaries: minimum spend, 0%, 100%, stacked | Behaviour matches the discount rules in G4 | P2 | D-IV, G4 |
| A-04 | Save cart for later, then return | Cart restored with the same items and quantities | P2 | D-IV |
| A-05 | Guest checkout end to end | Order completes without account creation (scope per G10) | P2 | D-IV, G10 |
| A-06 | Guest cart merged into an account at login | Merge behaviour defined, no duplicates or lost items | P2 | G10 |
| A-07 | Cart handed to the payment gateway | Items, quantities, amounts and currency transmitted correctly | P2 | D-IV, G6 |
| A-08 | Successful payment | Cart cleared, order created with correct status | P2 | D-IV |
| A-09 | Failed or cancelled payment | Cart preserved; no order and no partial order written | P2 | D-IV |
| A-10 | Double-click / refresh at the payment step | No duplicate order (idempotency) | P2 | D-IV |

### 3.6 Cross-role & permission paths — blocked by G14

| ID | Scenario | Expected result | Pri | Trace |
| --- | --- | --- | --- | --- |
| R-01 | User A requests User B's cart id directly | Denied; no data leaked | P0 | G14 |
| R-02 | Guest session accesses a registered user's cart | Denied | P0 | G14 |
| R-03 | Each role (guest / registered / admin) views cart actions | Only permitted actions are offered and accepted | P1 | G14 |

These cannot be executed until G14 is answered — the authorization model is undefined.

---

## 4. Test Data & Environment

### 4.1 Environment (blocked — G3)

Not specified on the ticket. Needed before execution:

- Application URL and build/version under test; how the build is deployed.
- Browser and device matrix.
- Whether the shipping API and payment gateway have usable sandbox modes (G6).
- Access to logs / network inspection for verifying server-side totals.

### 4.2 Test data set required (blocked — G4)

To be supplied or seeded. Every row below is a request to the author, not a confirmed fixture.

| Entity | Variants needed | Status |
| --- | --- | --- |
| Products | In stock; low stock (1 left); out of stock; zero price; fractional price (e.g. 0.99); high price; 3-decimal price | To confirm |
| Cart states | Empty; single line; multi-line; quantity at max; very large quantity | To confirm |
| Coupons | Valid percentage; valid fixed amount; expired; invalid; minimum-spend; 100%; stackable | To confirm |
| Tax | Taxable; exempt; multiple rates; rate change mid-cart | To confirm |
| Shipping | Free-shipping threshold; per-weight; per-destination; per-method | To confirm |
| Currency | Single or multi; 0-dp currency (e.g. JPY) and 2-dp currency | To confirm |
| Users | Guest; registered; a second registered user for authorization tests | To confirm |
| Payment | Sandbox success; decline; timeout/cancel; 3-D Secure | To confirm |

### 4.3 Proposed matrices (to be approved)

- **Browsers:** latest Chrome, Edge, Firefox, Safari (and one prior major each).
- **Viewports:** 375 px (mobile), 768 px (tablet), 1440 px (desktop).

---

## 5. Risks & Assumptions

### Risks

| ID | Risk | Impact | Mitigation |
| --- | --- | --- | --- |
| R1 | No acceptance criteria (G1) | Scope disputes; requirements go untested | Obtain ACs or get Section 3 approved as the baseline before execution |
| R2 | Pricing/rounding defects (G18) | Financial loss and reputational damage | Hand-calculated verification for every money path; confirm server-side authority |
| R3 | Unnamed integrations (G6) | Shipping and payment scenarios blocked | Identify sandbox endpoints and test modes up front |
| R4 | "if applicable" conditions (G7–G11) | Untested paths shipped silently | Force an explicit in-scope / out-of-scope decision |
| R5 | Ticket status "In Review" (G17) | Requirements change mid-testing; rework | Freeze scope at execution start |
| R6 | No owner on the ticket (G17) | Questions stall; gaps stay unanswered | Assign an owner and a response expectation |
| R7 | No cart implementation in this repository | Cannot inspect code to confirm behaviour | Request repo/build access, or plan a black-box approach |
| R8 | Quantity/price trust on the client (G14) | Price tampering, cart manipulation | Confirm server-side recomputation and authorization |

### Assumptions

- A1: This is a web-based e-commerce cart; behaviour is observed through the browser.
- A2: The cart is authoritative server-side, and totals are recomputed rather than trusted from the client.
- A3: Everything listed in the ticket is intended to be tested, even where marked "Low Priority", unless the author defers it (G11).
- A4: Where the ticket says "if applicable", the default assumption is "in scope, behaviour to be defined" — no scenario is silently dropped.
- A5: The ticket description is the only requirement source; there is no linked design or spec to cross-check.
- A6: Money values use a 2-decimal currency unless told otherwise.

---

## 6. Entry / Exit Criteria

### Entry

- G1 and G3–G6 answered: acceptance criteria (or Section 3 approved), environment reachable, test data available, integrations usable in sandbox.
- Scope frozen with an explicit decision on the conditional features (G7–G11).
- An owner is assigned who can answer the Section 2 questions (G17).

### Exit

- All P0 scenarios pass.
- No open P0 or P1 defects.
- Subtotal, tax, shipping and total verified against independent hand calculations, with rounding documented.
- Authorization checks (R-01…R-03) pass, or are explicitly deferred with sign-off.
- Every gap in Section 2 is either resolved or recorded as an accepted, signed-off risk.

---

## HUMAN REVIEW GATE

**This plan is a draft and is not approved.** It stops here for a human to review.

**What I assumed (unconfirmed):**

- The scenario set is complete relative to the ticket description; nothing was dropped for the "if applicable" items — they are flagged instead.
- Priority ratings (P0/P1/P2) are my proposal from risk, not from the ticket.
- Expected results marked **Spec needed** were deliberately not invented.

**Open questions that block sign-off:**

- G1 — acceptance criteria, or approval of Section 3 as the baseline.
- G3–G6 — environment, test data, and named shipping/payment sandboxes.
- G13 — quantity bounds, and whether a quantity of 0 is an error or a removal.
- G14 — the authorization model, especially cart-id access control.
- G11 — which advanced features are in this release.
- G17 — who owns the ticket and will answer these questions.

**Next step:** please confirm, correct or extend the above. In particular, decide the
in/out-of-scope boundary for the conditional features and supply the Section 4 environment and
test data. I will not write test cases or automation from this plan until a human approves it.

_Waiting on approval — treat every priority and expected result above as provisional._
