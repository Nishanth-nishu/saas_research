# Competitor Acquisition Study: AI/Automation Agencies, Consultants, Freelancers, Small Vertical SaaS

Research date: 2026-10-28 (all pages accessed this date). Companion data: `research/COMPETITOR_ACQUISITION_STUDY.csv` (15 rows).

Labels follow `research/RESEARCH_RULES.md`: **FACT** (seen on an official/primary page), **VENDOR_CLAIM** (company's own marketing), **CUSTOMER_OPINION** (reviews, Reddit, forums), **HYPOTHESIS** (our interpretation). `snippet-only` = seen only in a search-result summary, page not opened.

---

## 1. Method

1. Sampled from **official partner directories** (Zapier Solution Partner directory at zapier.com/experts, Make Partners Directory, n8n Expert Partner page), **marketplaces** (Contra), and web searches for India-based n8n/Make/Zapier providers and niche agencies.
2. For each entity, opened the official site and/or official directory profile with WebFetch and recorded only what was visible. The directory profile fields (tier, minimum spend, budget bands, review count) are facts shown on Zapier's site, but the partner fills them in. Treat them as partner-declared.
3. Acquisition channels are recorded only where observable (directory listing, linked YouTube, lead magnet, marketplace listing). Cold email, ads and referrals cannot be observed from outside and are marked so.
4. For acquisition-channel evidence, I opened practitioner write-ups (Starter Story interview, Make Community thread, Reddit snapshot), benchmark pages (Instantly, EmailBison), and a vendor case study about Zapier's directory (PartnerPage). Some survey stats are secondhand via a compilation page because the primary page was blocked (see Limitations).

Mix achieved: **7 India-based** (Edesy, InfyOm, Msquare, DSP Solves, Zorven, 2 Contra freelancers, plus CallMissed as vertical SaaS = 8 rows), **7 international** (XRAY, Flow Digital, That Automation Agency, McBride Method, PromoPilot, Luhhu/Andrew Davison, Morningside AI). 9 entities have official Zapier/Make directory listings. Upwork profiles could not be fetched (403).

---

## 2. Per-company profiles

### India

**Edesy (edesy.in)** - confidence high
- FACT: Published INR prices: single n8n workflow ₹40,000; multi-flow ₹1,00,000; enterprise ₹2,50,000+; self-hosting from ₹35,000; Zapier/Make to n8n migration from ₹50,000; AI agent from ₹75,000; maintenance retainer ₹12,000-50,000/month. A paid AI strategy consultation costs ₹10,000 and is credited back against the project. The site promises a 30-min scoping call, then a fixed quote within 1 business day.
- FACT: The site names these targets: Indian SaaS startups (5-50 staff), D2C, real-estate brokers, EdTech, and BFSI/NBFC (KYC, collections). YouTube, LinkedIn and founder X/GitHub are linked. No case studies are shown.
- VENDOR_CLAIM: "Founder-led delivery", DPDP-compliant self-hosting, Indian-language workflows.
- HYPOTHESIS: This is the clearest Indian price anchor found. Positioning against Zapier cost plus Indian data rules (DPDP) is concrete, but the site shows no proof.

**InfyOm Technologies (Surat)** - medium
- FACT: No prices are published (quote on request). The site offers free n8n templates and ready-made vertical apps (clinic, POS, hospital). Engagements are either project-based or "hire a dedicated n8n expert".
- VENDOR_CLAIM: 100+ n8n workflows, 75+ projects, and a "Top Rated n8n company in India" label with no third-party source. Six testimonials and case studies, with no numbers.
- HYPOTHESIS: This is a typical Indian dev shop adding n8n. It competes on breadth, not niche.

**Msquare Automation Solutions (Thane / Kozhikode)** - high
- FACT: The site offers a free "Start Free Audit" scorecard and free Calendly consult. It sells its own Make custom apps. Make's India page names Msquare as a local partner. The Make directory lists it with Gold shown and a country label of Australia, while its own site and a Make Community post dated 2024-10-24 claim Platinum. The tier and country are inconsistent across sources.
- VENDOR_CLAIM: 650+ businesses, 1,000+ projects. Case results: 72% fewer order errors, 12-15+ hrs/week saved. "Make Automator of the Month" Jan 2022.
- HYPOTHESIS: An Indian team won international clients through the tool vendor's ecosystem: directory tier, community posts and published apps. This is the most replicable "India-to-global" pattern seen.

**DSP Solves (Gurugram)** - medium (directory only)
- FACT (Zapier directory): Silver tier, 2-4 staff, minimum spend $250, budget bands $100-$5,000, free 30-min call, 1 review (Jul 2025). Lists client logos including Godrej Properties and Findoc (VENDOR_CLAIM).

**Zorven (Bengaluru)** - medium (directory only)
- FACT: Silver tier, 5-15 staff, minimum $100, bands $100-$1,000, 1 review (Apr 2026). Positioned as a generalist "Shopify, websites, custom software, automation".

**Prathik Reddy (Contra, Kothagudem)** - medium
- FACT: Productised listing "Custom n8n / Zapier Automation in 7 Days", starting at **USD 800**. Includes a process map, a workflow of up to 20 steps, an LLM step, QA, Loom/PDF handoff and 7-day support. A separate "AI Lead Generation Engine" costs USD 1,500. The listing has no reviews.

**Sujal Singh (Contra, Lucknow)** - low
- FACT: "Contact for pricing" n8n/Make listing, 1-week timeline, no reviews.

**CallMissed (Pune) - small vertical SaaS** - medium
- FACT: AI receptionist across voice, WhatsApp and social channels in 22 Indian languages. Free tier of 1,000 credits with no card required. A live AI demo calls you. Billing is usage-based; structured data shows an offer range of INR 0-20,000. No testimonials. Founded 2026 per structured data.
- HYPOTHESIS: Indian SMB voice/WhatsApp AI is being commoditised by self-serve SaaS. Haptik's WhatsApp agents start at ₹10,000 (snippet-only, Business Today). A solo services founder should not sell "a WhatsApp bot" on price.

### International

**XRAY (xray.tech)** - high
- FACT: XRAY Hourly is **$250/hr**, sold in 4, 10 or 20-hr blocks per the directory. The Workflow Solution Design Sprint costs **$15,000**; the homepage labels this "Monthly $15,000/mo", which conflicts with the sprint page. Transformation is priced after assessment. 501(c)(3) organisations get preferred pricing. Lead magnets: a free assessment quiz, a free automation search engine and a grants page. The blog advertises "hundreds of free tutorials", and the site links a YouTube channel. Zapier Platinum with 111 reviews.
- VENDOR_CLAIM: Certified partner of Airtable, Claude, StackOne and Zapier. Testimonials have no figures.

**Flow Digital (Brooklyn)** - high
- FACT (Zapier directory): A **$297 75-minute implementation session**; free 20-min discovery call; minimum spend $100; 16-50 staff; **473 reviews** (5.0); slots booked 2-3 weeks out.
- VENDOR_CLAIM: 128% client revenue growth, SOC 2 Type II, named clients (MasterClass, Yelp).
- HYPOTHESIS: The cheap fixed session is a "tripwire" that converts directory visitors and generates reviews at volume.

**That Automation Agency (Brisbane)** - medium
- FACT (directory): Platinum, 2-4 staff, minimum $1,000, 37 reviews. The profile states "automation only".
- VENDOR_CLAIM: Runs "the largest Facebook Community for Zapier users", 375+ clients, using Zapier since 2009. I did not verify the Facebook group. The site content (fractional COO, Power BI, a "Chris Drake Automation" YouTube channel) only partly matches the directory description.

**McBride Method (Chattanooga)** - high
- FACT: Nonprofit niche, especially Big Brothers Big Sisters chapters. The founder is an ex-BBBS operator per the site. Offers include a **grant-fundable Nonprofit AI Assessment** and a for-profit assessment credited toward a build. Directory: minimum $1,000, bands up to $200k, US only, 9 reviews.
- VENDOR_CLAIM: One BBBS agency saw 49% faster inquiry-to-interview, 39% more interviews YoY and 17,000+ tasks automated. The site claims 33 nonprofits served across 8 states.
- HYPOTHESIS: This is the strongest niche example. An insider founder serves a federated network of near-identical organisations, so one case study is relevant to every chapter.

**PromoPilot (Oklahoma City)** - medium
- FACT (directory): "AI and automation for the print and promotional products industry". Names vertical apps (commonsku, Order Desk, Liftoff, Order My Gear). Minimum $1,000, bands $1,001-$10,000, 0 reviews. Client logos are VENDOR_CLAIM.

**Luhhu / Andrew Davison (UK, solo)** - high
- FACT: The site says "No sales or scoping calls" and offers a same-day written quote. It targets broken or half-built Zaps. Directory: Gold, 1 employee, **239 reviews**, minimum $100.
- Self-reported (Starter Story, Apr 2020): started on Upwork in Nov 2017 and got his first job within 12 hours at $20/hr. Later became a Zapier Certified Expert; the Experts directory and SEO became the main sources, at 1-3 inquiries per day. Revenue was $5.5-6.5K/month with fixed costs under $500. He left Upwork partly because of its 20% fee at the time.
- HYPOTHESIS: This is the most documented solo ladder: marketplace, then certification, then directory plus SEO, with async delivery. It is time-zone friendly for an Indian founder.

**Morningside AI** - medium
- FACT: No prices published. Targets enterprises. Claims 13.4M YouTube views, a 90k-member community and 2,700+ people through programs (VENDOR_CLAIM on site).
- Self-reported (Liam Ottley newsletter, 2024-11-18): it took him 14 months to make his first online profit. He recommends authority-building and content.
- HYPOTHESIS: The audience-first route works at scale but is slow.

---

## 3. Cross-cutting patterns

**Positioning**
- Most directory partners are tool-first ("Zapier/Make expert") and industry-agnostic. FACT: of the 31 featured Zapier partners on zapier.com/experts, only a few name a vertical: nonprofits (McBride), print/promo (PromoPilot), home-services voice AI (Golmtech) and Salesforce ecosystems.
- Niche players use the buyer's own vocabulary and named vertical apps (MatchForce, commonsku). HYPOTHESIS: this is what makes a niche credible.
- Indian providers are mostly generalists with long industry lists (InfyOm, Msquare, Edesy, Zorven). The exception is Edesy's India-specific angle: DPDP, Indian languages, LeadSquared and WhatsApp.

**Price bands observed (FACT unless noted)**

| Segment | Entry offer | Typical project | Retainer/top |
|---|---|---|---|
| India agencies (Edesy) | ₹10k paid consult (credited) | ₹40k single workflow; ₹1L multi-flow; ₹35-75k setups/agents | ₹12-50k/month; ₹2.5L+ enterprise |
| India Zapier partners (directory) | $100-$250 minimum spend | $100-$1,000 (Zorven) / up to $5,000 (DSP) | not stated |
| India freelancers (Contra) | $800 7-day productised build | $1,500 lead-gen engine | not stated |
| Intl solo/small (Luhhu, Flow Digital) | $100 min; $297 75-min session | $100-$5,000/$10,000 bands | hourly/retainer |
| Intl niche (McBride, PromoPilot, TAA) | $1,000 minimum spend | $1k-$10k; up to $200k bands | not stated |
| Intl premium (XRAY) | $250/hr in 4-20 hr blocks | $15,000 design sprint | transformation priced after assessment |

Third-party benchmarks (not verified; vendor/marketing pages, snippet-only): real-estate AI agencies charge $997-$2,500 setup plus $297-$997/month, and Enterprise DNA estimates $2k-$12k setup plus $750-$5k/month.

**Pilot/audit offers**
- Free discovery call (15-30 min) is near-universal on Zapier directory profiles (FACT). HYPOTHESIS: it is therefore not a differentiator.
- Differentiated entry offers seen:
  - Paid session that delivers a working result: Flow Digital $297.
  - Paid consult credited to the project: Edesy ₹10k; McBride for-profit assessment.
  - Grant-fundable assessment: McBride; XRAY grants page.
  - Free scorecard/quiz audit: Msquare, XRAY.
  - Async same-day quote with no call: Luhhu.
  - Fixed-scope 7-day productised build: Contra $800.

**Buyer roles targeted.** Owners and operators of SMBs (1-250 staff per directory filters) dominate. Specific roles named: nonprofit executives (McBride), marketing teams outgrowing Zapier and technical founders (Edesy), agency owners (Make thread), real-estate agents (Reddit). Enterprise "teams" are the target only at XRAY and Morningside.

**Proof.** Review counts concentrate heavily. Flow Digital has 473, Luhhu 239 and XRAY 111, while Indian Silver partners have 1 each and PromoPilot has 0 (FACT). Quantified case studies are rare: only Msquare, McBride and Flow Digital give numbers, all VENDOR_CLAIM.

---

## 4. Evidence-graded acquisition channels

Evidence type key: S = self-reported practitioner; V = vendor/platform claim; B = benchmark dataset (vendor-published); O = observed fact; 2nd = secondhand compilation.

| Channel | Evidence it works | Evidence type | Cost | Fit for solo founder in India |
|---|---|---|---|---|
| **Warm intros / referrals** | Make Community, 2026-09-24: ~30 warm-intro messages gave 2 clients, ~100 cold calls gave 0. SparkToro/Moogan 2025 survey of 612 agencies: 66% name client referrals their top source (2nd, via shno.co). RSW/US: discovery via networking fell from 73% (2022) to 58% (2025) (Agility PR). | S, 2nd | Low cash, high time | High for first 1-3 clients (IIITH network, ex-colleagues, startup founders); does not scale alone |
| **Tool-vendor partner directories (Zapier/Make)** | Zapier directory makes 500+ customer-to-expert matches/month across 400+ partners (PartnerPage case study). Luhhu called the directory a major source, at 1-3 inquiries/day with SEO (2020). Top partners hold 100-470 reviews, Indian Silver partners 1 each. | V, S, O | Certification effort; no listing fee observed | Medium-high. HYPOTHESIS: ~500 matches across 400+ partners averages about 1 per partner per month, skewed to top tiers, so expect little until reviews accumulate. n8n's Expert program is closed to India (eligibility: UK, IE, N. Europe, N. America; ≥3 active n8n customers) (FACT) |
| **Freelance marketplaces (Upwork, Contra)** | Luhhu got his first Upwork job within 12 hrs at $20/hr (2017) and later left over the 20% fee (S, 2020). Upwork fee is now variable 0-15% and Connects cost $0.15 (snippet-only; official page 403). A blog claims ~47 proposals per job within 24h (unverified). | S, snippet | Fees 10-20%; Connects; low rates early | High as a first-revenue and review engine from India (USD pricing); plan to migrate clients off-platform via direct contracts within rules |
| **Niche-specific cold DMs / cold email** | Reddit r/automation (~Nov 2025): 50 DMs to real-estate agents about 5-minute lead follow-up gave 3 replies and 1 client at $2,000/month (S). Instantly 2026: 3.43% average reply, top quartile 5.5%, $152.73 per meeting (B). Belkins strict method: 0.45% (B, via EmailBison). SparkToro/Moogan 2024: 6% of agencies name outbound their #1 source; 34% rate it not effective (2nd). | S, B, 2nd | Low cash (domains, tools ~$30-100/mo); high time | Medium. Works only with a narrow problem-led offer. HYPOTHESIS: at a 1-3% real reply rate, expect 1-3 conversations per 100 well-targeted sends |
| **Community participation (tool forums, FB groups)** | Luhhu answered on the Zapier community and Twitter early on (S). Msquare is visible in the Make Community and won "Automator of the Month" (O/V). That Automation Agency claims to run the largest Zapier FB group (V). The Make thread author believes community beats cold outreach, from reading only (S). | S, V | Time only | High. Free, async, and builds proof for directories |
| **SEO / service landing pages** | Luhhu named SEO a main source (S, 2020). Edesy runs a ranking "n8n developer india" page (O: it surfaced in search). AgencyAnalytics 2023: 16% of agencies get clients via own SEO (2nd). | S, O, 2nd | Time; slow (months) | Medium. Good compounding asset; target long-tail "X automation for Y in India" |
| **Founder content / YouTube / community** | Morningside AI claims 13.4M views and 90k community, and serves enterprise clients (V). Ottley: 14 months to first online profit (S). XRAY: hundreds of tutorials (O). | V, S, O | Very high time; slow | Low as the primary channel early; useful as a proof library (Loom demos) |
| **Lead magnets (audit scorecard, quiz, free templates)** | Observed at Msquare, XRAY and InfyOm (O). No conversion data found. | O | Low | Medium. Unproven; cheap to test |
| **Paid entry session / credited consult** | Flow Digital $297 session and 473 reviews (O, correlation only). Edesy ₹10k credited (O). | O | None | High. Easy to copy; filters tire-kickers |
| **Grant/subsidy-funded offers** | McBride "grant-fundable" assessment; XRAY grants page (O). | O | Low | HYPOTHESIS: Indian analogue may be MSME/startup schemes. Needs research |
| **LinkedIn posting** | Make thread: 1 post about a fixed production failure got 0 replies (S, n=1). LinkedIn reply-rate stats (10.3% outreach replies, Expandi) are secondhand. | S, 2nd | Time | Unclear; no strong evidence either way |
| **Paid ads** | No practitioner evidence found for small automation agencies | none | Cash | Not recommended on a tiny budget (no evidence) |

---

## 5. What seems ineffective, generic or expensive (with evidence)

1. **Generic "AI automation agency" positioning.** Reddit commenters say niching down "moved the needle" and that demo interest is not buying intent (CUSTOMER_OPINION, r/automation snapshot). Ciela.ai summarises Reddit threads as saying the generalist top segment is crowded (snippet-only, not opened).
2. **Unfocused cold calling / volume cold outreach.** ~100 cold calls produced 0 clients (Make Community, S, n=1). Belkins' strict reply-rate measure is 0.45%, and 34% of agencies rate outbound not effective (2nd).
3. **Free work.** "Free work attracts tire-kickers" (Reddit comment, CUSTOMER_OPINION; the commenter promotes a product). A counter-example exists: an n8n forum freelancer offers a free case in exchange for a testimonial and case study (snippet-only).
4. **Directory listing without reviews.** Indian Silver partners have 1 review each and PromoPilot has 0, versus 100-470 for top partners (O). HYPOTHESIS: a listing alone is not a channel; reviews drive ranking ("sort by tier and review count", O).
5. **"Contact for pricing" on marketplaces** with no reviews (Sujal Singh listing, O). HYPOTHESIS: weaker than fixed-price productised listings.
6. **Course/guru-driven playbooks.** A newsletter author who sells automation says "99% of AI automation content… is BS" (snippet-only). Revenue anecdotes (Saraev ~$300k in 3 months; a "$20K/month solo operator") are self-reported or secondhand. One comes from a page that promotes the guru's paid community (howdoiuseai.com, opened).
7. **Expensive entry offers.** XRAY's $15k sprint and enterprise retainers are not reachable for a newcomer without proof (HYPOTHESIS).
8. **Templated city SEO pages** with no clients (Innovative AI Solutions, snippet-only). HYPOTHESIS: low trust.
9. **Competing on price in Indian SMB WhatsApp/voice bots**, where SaaS starts at ₹10k (Haptik, snippet-only) or free tiers (CallMissed, O).

---

## 6. Ten lessons (all HYPOTHESIS)

1. **HYPOTHESIS:** Pick one niche where a single case study transfers to many near-identical buyers, as McBride does with BBBS chapters. Indian candidates: real-estate brokers on LeadSquared/WhatsApp, coaching institutes, or CA firms. Use their app names on your page.
2. **HYPOTHESIS:** Get the first 1-3 clients from warm intros (IIITH alumni, startup founders), the only channel with converting evidence in the practitioner data. Ask each for a written, numbered testimonial.
3. **HYPOTHESIS:** Run a marketplace in parallel (Upwork/Contra) with a fixed-scope productised offer priced in USD ($500-$1,000, like the $800 7-day build) to earn reviews and cash. Expect fees of 10-20%.
4. **HYPOTHESIS:** Earn Zapier and/or Make certification and a directory listing early, but treat it as a review-accumulation game. The n8n Expert program currently excludes India.
5. **HYPOTHESIS:** Copy the paid low-ticket entry offer: a $99-$300 or ₹5-15k "fix one workflow in 75 minutes" session, or a paid audit credited to the build. Avoid free audits for strangers.
6. **HYPOTHESIS:** For outbound, use problem-led messages to one niche, e.g. "lead follow-up in 5 minutes for brokers". Budget for 1-3% replies and 3-4 touches per sequence (Instantly: 42% of replies come after step 1).
7. **HYPOTHESIS:** Publish INR and USD price anchors, as Edesy does. Indian bands seen are ₹40k-₹1L per project and ₹12-50k/month retainers; international small-firm minimums run $100-$1,000.
8. **HYPOTHESIS:** Offer async, call-free quoting (the Luhhu model) to serve US/UK clients across time zones from India.
9. **HYPOTHESIS:** Lead with India-specific differentiators where selling domestically: DPDP-compliant self-hosting, Indian-language LLM flows, and LeadSquared/Zoho/WhatsApp integrations. Do not sell a commodity WhatsApp bot.
10. **HYPOTHESIS:** Treat community answers, templates and Loom demos as the proof library behind every channel. Don't make YouTube or audience-building the primary channel: the best-known example took 14 months to first profit.

---

## 7. Limitations and failed fetches

- **Failed or blocked fetches:**
  - https://www.flowmondo.com/ returned 403 (not profiled).
  - https://support.upwork.com/hc/en-us/articles/211062538-Freelancer-Service-Fees returned 403, so Upwork fee figures are snippet-only.
  - https://www.upwork.com/hire/n8n-developers/in/ and https://www.upwork.com/hire/zapier-developers/us/ returned 403, so no Upwork freelancer profiles were captured.
  - https://sparktoro.com/blog/digital-agency-new-business-still-a-concern-referrals-still-rule-for-lead-gen-and-are-sales-pipelines-finally-recovering/ returned 403, so the SparkToro/Moogan figures are secondhand via shno.co.
  - https://www.businessautomated.com/ returned HTTP 530.
  - https://zapier.com/resources/webinar/zap-sharing returned 404. The claim that Heather Satterley reached $250K via shared Zaps is snippet-only.
  - https://zapier.com/partnerdirectory/partner/dsp-solves returned 404; the alternate /dspsolves worked.
  - https://growwstacks.com/contact returned an empty page, so country is unconfirmed and GrowwStacks was excluded.
  - https://mondayagents.gumroad.com/l/aiagents returned only its title. The "$2,499/month unlimited automations" subscription is snippet-only and excluded.
  - https://golance.com/blogs/upwork-fees-explained-2026 contained no Upwork fee data.
  - The Zapier Experts program page did not show tier criteria or partner fees.
- **Data quality:**
  - Directory fields are partner-declared.
  - Msquare's tier and country conflict between the Make directory (Gold, Australia) and its own claims (Platinum, India addresses).
  - That Automation Agency's site content only partly matches its directory profile.
  - XRAY's $15k is labelled both "monthly" and "sprint".
- **Not observable:** Cold email, ads, referrals and LinkedIn DMs used by these firms cannot be seen from outside. No firm-level conversion data exists in public.
- **Practitioner evidence:** These are mostly single anecdotes (n=1) or secondhand. Revenue claims (Saraev, "$20K/month operator", Luhhu 2020) are self-reported and unverified. Luhhu's data is from 2020 and may not reflect 2026 directory dynamics.
- **Gaps:**
  - No verified per-partner lead counts from Zapier, Make or n8n directories.
  - No Indian-market practitioner data with numbers.
  - No coaching- or logistics-specific agency found with enough public evidence.
  - Next steps: Make directory filtered to India, Upwork profiles via browser, and Indian founder podcasts/interviews.

---

## Sources (accessed 2026-10-28)
- https://edesy.in/services/n8n-developer-india
- https://infyom.com/services/n8n-workflow-automation-services
- https://msquare.pro/
- https://community.make.com/t/big-news-msquare-is-now-a-platinum-partner-with-make-top-three-partners-in-the-world/58788
- https://www.make.com/en/automation-india
- https://www.make.com/en/partners-directory
- https://n8n.io/experts/
- https://zapier.com/experts
- https://zapier.com/partnerdirectory/partner/dspsolves
- https://zapier.com/partnerdirectory/partner/zorven
- https://zapier.com/partnerdirectory/partner/flow-digital
- https://zapier.com/partnerdirectory/partner/that-automation-agency
- https://zapier.com/partnerdirectory/partner/mcbride-method
- https://zapier.com/partnerdirectory/partner/promopilot
- https://zapier.com/partnerdirectory/partner/andrewjdavison
- https://contra.com/s/eZEXgbFs-ai-powered-workflow-custom-n8n-zapier-automation-in-7-days
- https://contra.com/s/7QYcXe36-ai-workflow-automation-with-n8n
- https://www.callmissed.com/
- https://www.xray.tech/
- https://www.xray.tech/xray-monthly
- https://thatautomationagency.com/
- https://www.mcbridemethod.com/
- https://luhhu.com/zapier-expert/
- https://www.starterstory.com/zapier-agency
- https://www.morningside.ai/
- https://morningsideai.beehiiv.com/p/the-end-of-the-aaa-goldrush-9587
- https://www.partnerpage.io/customers/how-zapier-built-a-self-service-expert-marketplace-that-matches-more-than-500-customers-monthly
- https://community.make.com/t/what-actually-works-for-finding-automation-work-heres-my-data-so-far/115845
- https://reddit.sentinel-team.org/posts/1t8unqg/snapshots/2026-05-15T20%3A49%3A13.68504Z (r/automation archive snapshot, 2026-05-15 20:49 UTC / 2026-05-16 02:19 IST)
- https://instantly.ai/blog/email-sequence-benchmarks-2026-whats-a-good-open-rate-reply-rate-and-cost-per-meeting/
- https://emailbison.com/blogs/cold-email-open-rates
- https://www.shno.co/marketing-statistics/client-acquisition-statistics-for-agencies
- https://www.agilitypr.com/pr-agency-news/new-rsw-us-2026-outlook-report-finds-referrals-and-networking-losing-effectiveness-agencies-must-take-a-more-proactive-approach-to-new-business/
- https://howdoiuseai.com/blog/2026-07-16-how-a-solo-operator-hit-20k-a-month-in-ai-automati
- https://theaipimpclub.beehiiv.com/p/what-i-learned-coaching-723-ai-agency-founders
- https://www.zapier.com/blog/smartclick-systems-automates-millions-in-revenue
- Snippet-only: Haptik ₹10,000 (businesstoday.in); Upwork variable fee 0-15% and Connects (jobbers.io); Saraev revenue claims (goodreads repost); ciela.ai Reddit summaries; sentient-chatgptricks newsletter; MondayAgents $2,499/mo.
