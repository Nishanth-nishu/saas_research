# Competitive analysis: Segments C and D

This note covers the top two workflows in each segment. Access date for all sources: 2026-10-28. Row-level detail and source URLs are in `competitors_CD.csv`. Claim IDs (C1, D2 and so on) refer to the findings tables in `market_CD.md`.

Each workflow is split into **Facts** (seen on official pages, or customer reviews labelled as opinion) and **Hypotheses** (our interpretation, not validated).

---

## C-W1: Agency client reporting with AI commentary

**Facts**
- There is a clear tier ladder of dedicated tools:
  - Swydo: EUR 62–69/mo plus a per-source fee.
  - DashThis: USD 44–429/mo.
  - AgencyAnalytics: USD 20 per client per month, annual.
  - Supermetrics: USD 39–159/mo, for Looker Studio and Sheets pipelines.
  - Whatagraph: from EUR 699/mo, annual. (C1, C3–C6)
- Every one of these tools now includes AI summaries or agents:
  - AgencyAI and MCP (AgencyAnalytics)
  - Whatagraph IQ and IQ Agents
  - DashThis AI Insights, with free and PRO tiers
  - Swydo AI summaries, which consume credits
- Customer complaints concentrate on billing and support, not on missing features:
  - AgencyAnalytics: billing for deleted clients; slow support (Trustpilot).
  - Whatagraph: auto-renewal, deactivated reports, aggressive sales (Trustpilot 2.5/5). (C9, C10)
- Building a reporting SaaS that reads Google Ads data requires API access approval. Basic access needs brand verification. Standard access needs a manual audit and Required Minimum Functionality. Developer tokens were "sunset" on 2026-09-09 in favour of per-project access. (C11)
- Coupler describes the manual workflow as: export, screenshot, run through AI, check the AI's numbers, write context, format. (C7, vendor blog)

**Hypotheses**
- A standalone reporting SaaS from a solo founder would compete against roughly USD 20/client incumbents that already have AI. Differentiation is weak (score 2/5).
- A narrower implementation pilot could still sell: an AI commentary and QA layer that sits on top of the agency's existing AgencyAnalytics, Supermetrics or Looker Studio data. It would write client-specific narrative in the agency's voice and flag anomalies. This sidesteps ad-API audits.
- Complaints about vendor billing and support suggest some agencies may value a responsive human implementer. This rests on a thin sample: about 40 Trustpilot reviews, with Reddit and G2 unavailable.
- Switching costs are moderate. Report templates and client logins are tied to the tool, so an add-on positioning is lower-friction than replacement.

## C-W2: Proposal, SOW and RFP drafting from past content

**Facts**
- RFP-response software is enterprise-oriented:
  - Loopio publishes no prices, and its smallest tier includes 10 seats.
  - AutoRFP.ai reportedly starts at USD 899/mo on an annual term (snippet-only, third party).
  - Loopio's benchmark describes 33 h per RFP, 9 contributors and 166 RFPs a year. (C12–C14)
- SMB proposal tools focus on document design and e-sign, and put AI behind upper tiers or MCP hooks:
  - Proposify: Build USD 39/user annual; Scale has a USD 12,800/yr platform fee.
  - Qwilr: AI Prefill only on Scale, which needs 10 users. (C15, C16)
- Indian AI development agencies list USD 25–49/hr, with minimum projects ranging from USD 1k to 25k+ (snippet-only, Clutch). (C21)
- PandaDoc pricing could not be fetched (HTTP 429).

**Hypotheses**
- There may be a gap between "copy-paste into ChatGPT" and "USD 10k+/yr RFP platform" for 10–200-person IT services firms and dev shops. A RAG pilot over past proposals, case studies, CVs and security answers would fill it. Its output would be first drafts of SOWs, RFP answers and security questionnaires.
- This matches the founder's RAG skills and has high value per document.
- Main unknowns:
  - How often small firms actually respond to RFPs. The Loopio sample is RFP teams, not small shops.
  - Whether they will share confidential past bids with a solo vendor. Security trust is a barrier.
- Competitive intensity is high at the enterprise level and unclear at SMB level (score 3/5).

---

## D-W1: WISMO and order changes for D2C brands

**Facts**
- Native helpdesk AI already acts on Shopify orders. The Gorgias AI Agent can cancel orders, edit addresses, remove or replace items and reship, at USD 0.90–1.00 per automated interaction. (D1, D2)
- The Gorgias docs state the limit: these changes do not propagate to 3PLs or fulfillment apps, except through ShipStation, ShipMonk or ShipBob actions. (D2)
- Proactive tracking apps reduce WISMO before tickets arrive. CWILL (formerly ParcelPanel), from an India-based developer, has 3,197 reviews averaging 5.0 and is free up to 20 orders a month. (D7)
- India has low-cost WhatsApp-native options:
  - Interakt: from INR 2,799/mo, with Shopify order notifications and COD-to-prepaid flows; AI add-on about INR 2.5–3k/mo.
  - Gallabox: from INR 2,399/mo.
  - LimeChat: serves large D2C brands; no published price. (D8–D10)
- Shopify App Store reviews of Gorgias in 2026 complain about AI agent quality ("hallucinates", "half baked"), overage charges and support. Tidio reviews complain about pricing complexity and onboarding. (D5, D6, CUSTOMER_OPINION)
- Apps that touch customer names or addresses must meet Shopify's Level 2 protected-data requirements. (D25)

**Hypotheses**
- Generic WISMO automation is commoditised, with differentiation at 1/5.
- Residual openings for a solo implementer:
  - Brands whose order truth lives outside Shopify: Indian 3PLs, Shiprocket, Unicommerce, courier portals, or WooCommerce plus custom stacks.
  - Multi-system returns and RTO/COD logic.
  - Fixing poorly configured Gorgias or Tidio deployments, given the AI-quality complaints.
- These openings are all unvalidated.
- In India, low support salaries (about INR 2.6L/yr average base, D24) plus cheap WhatsApp tools cap what a brand will pay. Pilots might fit international Shopify brands better, where tickets cost USD 2.70–5.60 (D3, secondary).

## D-W2: Small-SaaS support deflection, triage and knowledge retrieval

**Facts**
- Outcome-based AI pricing from incumbents is now about USD 0.75–2.00 per resolution:
  - Help Scout: USD 0.75
  - Intercom Fin: USD 0.99
  - Plain: about USD 1, by our arithmetic from credits
  - Zendesk: USD 2.00 pay-as-you-go
  - Freshdesk: USD 49 per 100 sessions after the first 500
- Self-serve RAG bots such as Chatbase start at USD 32/mo. (D12–D20)
- Triage is a native feature:
  - Zendesk intelligent triage requires Professional and Copilot, and classifies only on the subject and first comment.
  - Plain lists urgency detection and auto-labelling. (D16, D20)
- Intercom gets Trustpilot complaints about cost and support, but this is a small sample (13 reviews). (D14)

**Hypotheses**
- Head-to-head competition with Fin or Zendesk AI is not viable for a solo founder (differentiation 1/5).
- Possible niches:
  - Implementation services for teams that bought a helpdesk AI and got poor results: content cleanup, knowledge-base gap analysis, eval harnesses.
  - Custom actions such as account lookups and plan changes.
  - Internal knowledge retrieval for support agents across docs, Slack and Jira, which helpdesk AIs may cover only partially. Not verified.
- Switching costs from the helpdesk are high, so any offer must integrate with the existing helpdesk rather than replace it.

---

## Cross-cutting competitive notes
- **Workflow automation platforms** (Zapier from USD 19.99/mo, n8n from EUR 20/mo or self-hosted free) are both substitutes and the founder's likely delivery tools. They keep implementation pilots cheap but lower the barrier for competitors (FACT pricing; HYPOTHESIS implication).
- **AI agencies and freelancers:** Indian firms list USD 25–49/hr (snippet-only). Marketplace rates on Upwork and Fiverr could not be fetched (403).
- **Manual alternatives:** in India, a support executive's average base pay is about INR 2.6L/yr (Payscale). In the US, a customer service rep's median pay is USD 44,770 (BLS). The labour-cost gap means the ROI story differs sharply by market (HYPOTHESIS).
- **Evidence gaps:** Reddit, G2 and Capterra were blocked, so customer frustration evidence is limited to Trustpilot and Shopify App Store reviews. Competitive conclusions should be re-tested with direct buyer conversations, which are outside this research's no-contact rule.
